import django_filters
import time
import logging
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets, filters
from datetime import datetime

from data_points.signals import custom_signal_for_aws_queue
from student_activity.auth import JWTAuthentication, AllowContentWriting, StudentPermission
from bson import ObjectId
from .models import ChallengeConfig, AdvanceFilterConfig, ChallengeData, StudentChallengeData
from .serializers import ChallengeConfigSerializer, AdvanceFilterConfigSerializer, ChallengeDataSerializer, \
    StudentChallengeDataSerializer
from challenges.utils import field_validation, upload_file_on_s3, get_start_end_dates, get_operator
from django.utils import timezone as django_timezone
from utils.common_methods import logger


class ChallengeConfigViewSet(viewsets.ModelViewSet):
    queryset = ChallengeConfig.objects.all()
    serializer_class = ChallengeConfigSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ['challenges', 'sub_challenges']
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        """
        This method is overwritten to cache response on query_param basis with expiry set to 24h
        returns:
            when challenges=true, then challenges list
            when sub_challenge=true, then sub_challenge list filtered with challenges
            when challenge and subchallenge both has value filter with the same
        """
        data = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(data, many=True)

        required = request.query_params.get('required', None)
        # get unique challenges
        if required == "challenges":
            unique_challenges = []
            for item in serializer.data:
                challenge = item['challenges']
                if challenge not in unique_challenges:
                    unique_challenges.append(challenge)
            response_data = unique_challenges

        # get unique sub_challenges
        elif required == "sub_challenges":
            unique_subchallenges = []
            for item in serializer.data:
                subchallenge = item['sub_challenges']
                if subchallenge not in unique_subchallenges:
                    unique_subchallenges.append(subchallenge)
            response_data = unique_subchallenges

        # get data with challenges and sub_challenges filter
        else:
            response_data = serializer.data

        return Response({"message": "success", "response": response_data, "status": status.HTTP_200_OK})


class AdvanceFilterConfigViewSet(viewsets.ModelViewSet):
    queryset = AdvanceFilterConfig.objects.all()
    serializer_class = AdvanceFilterConfigSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ['user_type', 'timeframe', 'value']
    http_method_names = ['get', 'post']

    def list(self, request, *args, **kwargs):
        """
            This method is used to get list of user_type, timeframe, value, comparison_operator
            returns:
            when required=user_type, then returns user_type list
            when required=timeframe, then returns timeframe list filtered with user_type
            when required=value, then returns value list filter with user_type and timeframe
            when required=comparison_operator, then returns comparison_operator filtered with user_type, timeframe and value
        """
        try:
            data = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(data, many=True)
            required = request.query_params.get('required', None)
            field_mapping = {
                "user_type": "user_type",
                "timeframe": "timeframe",
                "value": "value",
                "comparison_operator": "comparison_operator"
            }
            required_field = field_mapping.get(required)

            if not required_field:
                raise Exception(
                    f"{required} does not exists, choices for required are: [user_type, timeframe, value, comparison_operator]")

            if required_field == "value":
                response_data = []
                for item in serializer.data:
                    if {"unit_value": item["value"], "actual_value": item["actual_value"]} not in response_data:
                        response_data.append({"unit_value": item["value"], "actual_value": item["actual_value"]})

            else:
                response_data = list(set(item[required_field] for item in serializer.data))
            return Response({"message": "success", "response": response_data, "status": status.HTTP_200_OK})

        except Exception as e:
            return Response(
                {
                    "message": "failed",
                    "response": f"Error: {e}",
                    "status": status.HTTP_400_BAD_REQUEST}
            )


class ChallengeDataViewSet(viewsets.ModelViewSet):
    queryset = ChallengeData.objects.all()
    serializer_class = ChallengeDataSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filter_fields = ['challenge_title', 'status', 'start_date', 'end_date', 'district_id', 'board_id',
                     'class_id', 'medium_id', 'student_state_id', 'student_district_id', 'student_block_id']
    http_method_names = ['get', 'post', 'patch', 'delete']
    ordering_fields = ['created_at', 'updated_at', 'id', 'start_date', 'end_date']

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return ChallengeData.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    @staticmethod
    def json_field_key_validation(valid_data):
        missing = set()

        if valid_data.get('advance_filter', None):
            filter_keys = ['user_type', 'unit_key', 'unit_value']
            missing = field_validation(*filter_keys, **valid_data.get('advance_filter', {}))

        if valid_data.get('challenge_info'):
            challenge_info_keys = ['challenge', 'sub_challenge', 'comparison_operator', 'unit_key', 'unit_value']
            missing = missing.union(field_validation(*challenge_info_keys, **valid_data.get('challenge_info', {})))

        if valid_data.get('challenge_display'):
            display_keys = ['display_image', 'display_sub_title', 'display_description']
            missing = missing.union(field_validation(*display_keys, **valid_data.get('challenge_display', {})))

        if valid_data.get('after_success'):
            success_keys = ['success_image', 'success_sub_title', 'success_description']
            missing = missing.union(field_validation(*success_keys, **valid_data.get('after_success', {})))

        if missing:
            raise Exception(f'fields are required {missing}')

    @staticmethod
    def validate_time(start_date_utc, end_date_utc):

        if start_date_utc < django_timezone.now() or end_date_utc < django_timezone.now():
            return ('Start date and time cannot be before current date and time')

        # Validate end_date is not before start_date
        if end_date_utc < start_date_utc:
            return ('End date and time cannot be before start date and time')

    def create(self, request, *args, **kwargs):
        try:

            data = request.data
            field_missing = field_validation(
                'challenge_title', 'student_state_id', 'start_date',
                'end_date', 'reward_points', 'reward_message', 'challenge_info',
                'challenge_display', 'after_success', **data)
            if field_missing:
                raise Exception(f'fields are required {field_missing}')

            # key validation for json fields
            self.json_field_key_validation(data)

            data['created_by'] = self.request.user.user_id
            data['updated_by'] = self.request.user.user_id

            # add challenge_id
            last_challenge = ChallengeData.all_objects.order_by('-challenge_id').first()
            if last_challenge and last_challenge.challenge_id:
                data['challenge_id'] = last_challenge.challenge_id + 1
            else:
                data['challenge_id'] = 1

            serializer = ChallengeDataSerializer(data=data)
            serializer.is_valid(raise_exception=True)

            # save data
            serializer.save()
            return Response(
                {
                    "message": "Success",
                    "status": status.HTTP_201_CREATED,
                    "response": serializer.data
                }
            )

        except Exception as e:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {e.__traceback__.tb_lineno}, Error: {e}"
                }
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data
            if "status" in data:
                raise Exception("Cannot change status with this functionality")

            if instance.status in ['PUBLISHED', 'ACTIVE']:

                # if the status is 'PUBLISHED' only allow update for
                # [challenge_title,reward_message,challenge_display,after_success'] keys
                expected_keys = {'challenge_title', 'reward_message', 'challenge_display', 'after_success'}
                extra_keys = set(data.keys()) - expected_keys
                if extra_keys:
                    raise Exception("Update not allowed. can only update challenge_title, "
                                    "reward_message, challenge_display, after_success")

            if instance.status in ['EXPIRED']:
                raise Exception("Can not edit expired challenge")

            # key validation for json fields
            self.json_field_key_validation(data)

            # time validation
            if data.get('start_date', None) or data.get('end_date', None):

                if 'start_date' not in data or 'end_date' not in data:
                    # need both start_date and end_date if any one missing raise exception
                    raise Exception('Both start_date and end_date are required')

            # change updated_by
            data['updated_by'] = self.request.user.user_id

            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)

            # save the updated data
            serializer.save()

            return Response(
                {
                    "message": "Success",
                    "status": status.HTTP_200_OK,
                    "response": serializer.data
                }
            )
        except Exception as e:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": str(e)
                }
            )

    @action(methods=['post'], detail=False)
    def upload_challenge_images(self, request, **kwargs):
        """
        This api will upload challenge image to s3 and return cdn_url
        :param request:
        :param kwargs:
        :return:
        """
        data = request.data
        missing_fields = field_validation('image', **data)
        if not missing_fields:
            image = request.FILES['image']
            key = f'challenges/{int(time.time())}_{image.name}'
            image_type = image.name.split('.')[1]
            cdn_file_url = upload_file_on_s3(file=image, file_path=key, file_type=image_type, content_type="image")
            return Response({"message": "upload successful", "status": 200, 'file': cdn_file_url})
        else:
            return Response({"detail": f"{missing_fields} are required fields", "status": 400})

    @action(methods=['post'], detail=True)
    def publish_challenge(self, request, *args, **kwargs):
        try:
            """
            :param request:
            :param  args:
            :param kwargs:
            :return:
            """
            ai_generated = False
            pk = ObjectId(kwargs.get('pk'))
            standard_filter_fields = ['district_id', 'board_id', 'class_id', 'medium_id', 'student_state_id',
                                      'student_district_id', 'student_block_id', 'school_id']
            instance = self.get_object()

            time_validation_err = self.validate_time(instance.start_date, instance.end_date)
            if time_validation_err:
                raise Exception(time_validation_err)

            filter_pipeline = []
            filter_fields = ChallengeData.objects.filter(_id=pk).values(*standard_filter_fields).first()
            filter_fields = {f'{k}_id': v for k, v in filter_fields.items() if v}

            if school_value := filter_fields.get('school_id_id', False):
                filter_fields['school_id_id'] = {'$in': school_value}
            instance.filter_condition = filter_fields
            ad_filter = dict(instance.advance_filter)

            # advance filter exist create aggregation pipeline for EarnPoints and find students
            if ad_filter and ad_filter.get('user_type') == "Inactive User":
                # 1 filter with other available fields.
                filter_pipeline.append({'$match': filter_fields})

                # 2 lookup with time point
                filter_pipeline.append({
                    '$lookup': {
                        'from': "data_points_studentelementtime",
                        'localField': "student_id",
                        'foreignField': "student_id",
                        'as': "result",
                    },
                })
                # 3 unwind
                filter_pipeline.append({
                    '$unwind': {
                        'path': "$result",
                        'preserveNullAndEmptyArrays': True,
                    }
                })
                # 4 $set values
                filter_pipeline.append({
                    '$set': {
                        "result.user_id_id": "$user_id_id",
                        "result.student_id": "$student_id",
                        "result.created_at": {
                            '$ifNull': ["$result.created_at", "$created_at"],
                        },
                    }
                })
                # 5 $match
                end_date = get_start_end_dates(ad_filter.get('time_frame'), filter_dates=False)
                filter_pipeline.append({
                    '$match': {
                        "result.created_at": {
                            '$gt': end_date
                        },
                    }
                })
                # 6 $replaceRoot
                filter_pipeline.append({
                    '$replaceRoot': {
                        'newRoot': "$result",
                    }
                })
                # 7 group
                filter_pipeline.append({
                    '$group': {
                        '_id': "$student_id",
                        'user_id_id': {
                            '$first': "$user_id_id",
                        },
                        'time': {
                            '$sum': "$time",
                        },
                    }
                })
                # 8 match
                filter_pipeline.append({
                    '$match': {
                        'time': {
                            '$lt': 1,
                        },
                    },
                })
                # 9 project
                filter_pipeline.append({
                    '$project':
                        {
                            'student_id': '$_id', 'user_id_id': 1
                        }
                })
            elif ad_filter and not ad_filter.get('user_type') == "Inactive User":
                # 1 add time filter for timeframe in EarnPoints collections.
                if ad_filter.get('time_frame', False):
                    get_dates_filter = get_start_end_dates(ad_filter.get('time_frame'))
                    filter_pipeline.append({'$match': get_dates_filter})

                # 2 Group by time and points
                filter_pipeline.append({
                    "$group": {'_id': '$student_id', 'time': {'$sum': '$time'}, 'point': {'$sum': '$points'}}
                })

                # 3 match with the required unit key
                compair_condition = get_operator(ad_filter.get('comparison_operator')) or '$gt'
                filter_pipeline.append(
                    {'$match': {f"{ad_filter.get('unit_key')}": {f'{compair_condition}': ad_filter.get('unit_value')}}})

                # 4 Join with Student Profile table for the other required filter match
                filter_pipeline.append({
                    '$lookup': {
                        'from': "Students_App_studentprofile",
                        'localField': "_id",
                        'foreignField': "student_id",
                        'as': "studentprofile",
                    }})
                # 5 unwind (to get an object instead of an array)
                filter_pipeline.append({'$unwind': {'path': "$studentprofile"}})

                # 6 replace root
                filter_pipeline.append({'$replaceRoot': {'newRoot': '$studentprofile'}})

                # 7 filter with other available fields.
                filter_pipeline.append({'$match': filter_fields})

            instance.advance_filter_condition = filter_pipeline
            if instance.challenge_info.get('sub_challenge') in ['AI Reels In One Session', 'AI Reels Total']:
                ai_generated = True

            instance.challenge_info['ai_generated'] = ai_generated
            instance.status = 'PUBLISHED'
            instance.save()

            return Response(
                {
                    "message": "Success",
                    "status": status.HTTP_200_OK,
                }
            )
        except Exception as err:
            return Response(
                {
                    "message": "Failed",
                    "response": f"Error: {err}",
                    "status": status.HTTP_400_BAD_REQUEST,
                }
            )


class StudentChallengeDataViewSet(viewsets.ModelViewSet):
    queryset = StudentChallengeData.objects.all()
    serializer_class = StudentChallengeDataSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filter_fields = ['status', 'challenge_status', 'user_id', 'student_id']
    http_method_names = ['get', 'post']
    ordering_fields = ['created_at', 'completed_at', 'challenge__end_date']
    ordering = ['-created_at']

    @action(methods=['post'], detail=False)
    def accept_challenge(self, request):
        """
        This API is used by App to accept challenge by student
        """
        try:
            data = request.data
            missing = field_validation('student_id', 'challenge_id', **data)
            if missing:
                raise Exception(f'fields required {missing}')
            student_id = data.get('student_id')
            challenge_id = ObjectId(data.get('challenge_id'))

            student_challenge_obj = StudentChallengeData.objects.filter(student_id=student_id,
                                                                        challenge_id=challenge_id).first()
            if not student_challenge_obj:
                raise Exception(f'no records found for student_id: {student_id} and challenge_id: {challenge_id}')

            if student_challenge_obj.status == "SENT" and student_challenge_obj.challenge_status == "ACTIVE":
                student_challenge_obj.status = 'ACCEPTED'
                student_challenge_obj.accepted_at = datetime.now()
                student_challenge_obj.save()
            else:
                raise Exception(f'This challenge is either expired or is not sent to the student')
            logger.log_info(f"Challenge {challenge_id} Accepted by student {student_id}")

            # send custom signal for nudges
            signal_data = student_challenge_obj.__dict__
            removed_fields = ['_id', '_state', 'created_at', 'updated_at']
            signal_data['accepted_at'] = str(signal_data.get('accepted_at'))
            signal_data['challenge_id'] = str(signal_data.get('challenge_id'))
            [signal_data.pop(i, None) for i in removed_fields]
            custom_signal_for_aws_queue.send(
                sender="Challenge",
                instance=signal_data
            )
            return Response(
                {
                    "message": "Success",
                    "status": status.HTTP_200_OK,
                    "response": "status updated"
                }
            )

        except Exception as err:
            logger.log_error(f"Error on line {err.__traceback__.tb_lineno},Error: {err} in challenge Accept.")
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {err.__traceback__.tb_lineno},Error: {err}",
                }
            )
