import calendar
import json
import django_filters
import datetime
import time
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.core.cache import cache
from django.db.models import Sum, Count
from student_activity.auth import JWTAuthentication, AllowContentWriting, StudentPermission
from .models import (ReelsAttempt, StudentElementTime,
                     PartsProgress, ChapterParts, StudentTimePoints, Diamond,
                     Milestones, McqFirstAttempt, McqBestAttempt, ElementData, StudentMilestone, MILESTONES_CHOICES,
                     DailyStreak, DailyReward)
from .serializers import (ReelsAttemptSerializer, StudentElementTimeSerializer, PartsProgressSerializer,
                          StudentTimePointsSerializer, MilestonesSerializer, StudentMilestonesSerializer,
                          McqFirstAttemptSerializer,
                          McqBestAttemptSerializer, DiamondSerializer, DailyStreakSerializer)
from challenges.utils import field_validation
from bson import ObjectId
from student_activity.redis_sync import student_element_wise_time_sync, student_total_points_sync, \
    student_total_diamond_sync
from data_points.utils import add_points_to_student
from data_points.models import StudentProfile, ChapterProgress
from .filters import MilestoneFilters
from utils.common_methods import custom_mongo_client
from utils.common_methods import logger
from .signals import custom_signal_for_aws_queue
# from nudges.nudges_factory.nudges_factory import NudgesFactory


@api_view(['GET'])
def health(request):
    # data = {
    #           "user_id": 178604,
    #           "chapter_id": 554,
    #           "subject_id": 212,
    #           "class_id": 49,
    #           "time": 0,
    #           "points": 0,
    #           "percentage": 20
    #         }
    # NudgesFactory(student_id=114876, action='ChapterProgress', **data)
    return Response({"message": "success"})


class ReelsAttemptViewSet(viewsets.ModelViewSet):
    queryset = ReelsAttempt.objects.all()
    serializer_class = ReelsAttemptSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    http_method_names = ['get', 'post']

    def create(self, request, *args, **kwargs):
        # add points and time to StudentTimePoints collection
        add_points_to_student(
            points=request.data.get('correct'),  # 1 correct ans = 1 point
            time=request.data.get('time'),
            user_id=request.user.user_id,
            student_id=request.data.get('student_id'),
            point_activity="reels_attempt"
        )
        request.data['points'] = request.data.get('correct')
        return super().create(request, *args, **kwargs)


class StudentElementTimeViewset(viewsets.ModelViewSet):
    queryset = StudentElementTime.objects.all()
    serializer_class = StudentElementTimeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    http_method_names = ['get', 'post']

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return StudentElementTime.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    @action(methods=['post'], detail=False)
    def set_element_wise_time(self, request, *args, **kwargs):
        """
        This API is used by app to store the elements completed by a particular student
        Only completed elements are sent and the time and coins are stored in db element wise
        In redis it is stored as a list, If the list already exist for the same part it is updated with the new elements
        """
        try:
            elements_time_list = request.data.get('elements_time_list', [])
            print(elements_time_list)

            time_point_data = {'points': 0, 'time': 0}
            if not elements_time_list:
                return Response({"error": "No elements provided in the request."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if all required keys are present in each element
            for element_data in elements_time_list:
                field_missing = field_validation('user_id', 'student_id', 'element_id', 'element_type', 'class_id',
                                                 'subject_id', 'chapter_id', 'part_id', 'time',
                                                 **element_data)
                try:
                    element_obj = ElementData.objects.get(unique_id=element_data['element_id'])
                    if element_obj.time <= element_data['time']:
                        element_data['points'] = element_obj.points
                        element_data['time'] = element_obj.time
                except Exception as err:
                    print(err)

                if field_missing:
                    raise Exception(f'fields are required {field_missing} in element_id: {element_data["element_id"]}')

            for data in elements_time_list:
                collection = custom_mongo_client.get_collection('data_points_studentelementtime')
                ele_time = data.pop('time', 0)
                ele_points = data.pop('points', 0)

                criteria = {
                    "student_id": data.pop('student_id'),
                    "user_id": data.pop('user_id'),
                    "element_id": data.pop('element_id'),
                }
                update_values = {
                    "$set": {
                        'updated_at': datetime.datetime.utcnow(),
                        **data
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow(),
                        'time': ele_time,
                        'points': ele_points
                    }
                }
                updated_data = collection.update_one(criteria, update_values, upsert=True)
                signal_data = data
                signal_data.update(criteria)
                custom_signal_for_aws_queue.send(
                    sender="StudentElementTime",
                    instance={**signal_data}
                )
                if not updated_data.modified_count:
                    time_point_data['time'] += ele_time
                    time_point_data['points'] += ele_points

            # Save the list of saved elements in Redis
            user_id = request.user.user_id
            parts_id = request.data.get('parts_id')
            student_id = request.data.get('student_id')
            # add points and time
            add_points_to_student(
                points=time_point_data.get('points'),
                time=time_point_data.get('time'),
                user_id=user_id,
                student_id=student_id,
                point_activity="parts_progress"
            )

            redis_key = f"part_progress:{user_id}_{student_id}_{parts_id}"
            redis_data = student_element_wise_time_sync.get_data(key=redis_key)
            if redis_data:
                redis_data.extend(elements_time_list)
            else:
                redis_data = elements_time_list

            student_element_wise_time_sync.upload_data(key=redis_key, value=redis_data)

            return Response({"message": "success", "status": status.HTTP_200_OK, "response": "Elements saved"})

        except Exception as e:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {e.__traceback__.tb_lineno}, Error: {e}"
                }
            )


class PartsProgressViewset(viewsets.ModelViewSet):
    queryset = PartsProgress.objects.all()
    serializer_class = PartsProgressSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    http_method_names = ['get', 'post']

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return StudentElementTime.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    def create(self, request, *args, **kwargs):
        """
        This will create or update parts wise progress data.
        when the part is completed(percentage=100) remove element_wise data from redis
        """

        try:
            part_progress_list = request.data.get('part_progress_list', [])
            logger.log_info(f'Part Progress is coming {part_progress_list} at {datetime.datetime.now()}')
            if not part_progress_list:
                return Response({"error": "No elements provided in the request."}, status=status.HTTP_400_BAD_REQUEST)
            collection = custom_mongo_client.get_collection('data_points_partsprogress')
            chapter_progress = 0
            for data in part_progress_list:
                user_id = data.pop('user_id')
                student_id = data.pop('student_id')
                part_id = data.pop('part_id')

                data['time'] = round(int(data['time']))

                # if instance update data and if instance = none then create data
                time.sleep(3)
                time_point_data = StudentElementTime.objects.filter(
                    part_id=part_id, student_id=student_id).aggregate(time=Sum('time'), points=Sum('points'))
                data['time'] = time_point_data.get('time') or 0
                data['points'] = time_point_data.get('points', 0) or 0

                criteria = {
                    "student_id": student_id,
                    "user_id": user_id,
                    "part_id": part_id,
                }
                data['percentage'] = float(data['percentage'])
                update_values = {
                    "$set": {
                        'updated_at': datetime.datetime.utcnow(),
                        **data
                    },
                    "$setOnInsert": {
                        "created_at": datetime.datetime.utcnow(),
                    }
                }
                updated_data = collection.update_one(criteria, update_values, upsert=True)
                signal_data = data
                signal_data.update(criteria)
                custom_signal_for_aws_queue.send(
                    sender="PartsProgress",
                    instance={**signal_data}
                )

                # when a part is completed delete corresponding redis data
                if data['percentage'] == 100:
                    redis_key = f"part_progress:{user_id}_{student_id}_{part_id}"
                    student_element_wise_time_sync.delete_data(key=redis_key)

                chapter_id = data.get('chapter_id')
                chapter_progress = ChapterProgress.objects.filter(student_id=student_id, chapter_id=chapter_id).first()

            return Response(
                {
                    "message": "success", "status": status.HTTP_200_OK,
                    "response": {"chapter_progress": chapter_progress.percentage}
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

    @action(methods=['get'], detail=False)
    def get_parts_progress(self, request, *args, **kwargs):
        """
        This api is used by app to get part progress for a particular student
        Returns:
            completed=True , when the part is 100% complete
            completed=False, when the part is 0% complete, i.e, The part has no element completed
            completed=False + element_wise_data, when part is partially complete, gets element wise data from redis
        """
        try:
            data = request.query_params
            field_missing = field_validation('part_id', 'student_id', **data)
            if field_missing:
                raise Exception(f'fields are required: {field_missing}')

            part_id = data.get('part_id')
            student_id = data.get('student_id')

            progress_obj = PartsProgress.objects.filter(part_id=part_id, student_id=student_id).first()

            if progress_obj:

                if progress_obj.percentage == 100:
                    # if progress_obj exists and percentage is 100, then complete = true
                    progress_response = {"completed": True}
                else:
                    # if progress_obj exists and percentage is not 100, then complete = False, but element data exist
                    # get the element data from redis
                    user_id = request.user.user_id
                    redis_key = f"part_progress:{user_id}_{student_id}_{part_id}"
                    redis_data = student_element_wise_time_sync.get_data(key=redis_key)
                    progress_response = {"completed": False, "progress": redis_data}

            else:
                # if progress_obj does not exist then no element is completed in that part
                progress_response = {"completed": False}

            return Response(
                {
                    "message": "success",
                    "status": status.HTTP_200_OK,
                    "response": progress_response
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


class StudentTimePointsViewSet(viewsets.ModelViewSet):
    queryset = StudentTimePoints.objects.all()
    serializer_class = StudentTimePointsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    http_method_names = ['get', 'post']

    @action(methods=["post"], detail=False)
    def daily_open(self, request, *args, **kwargs):
        try:
            user_id = request.user.user_id

            today_date = datetime.date.today().strftime("%Y-%m-%d")
            key = f"daily_open_{user_id}-{today_date}"

            if cache.get(key):
                response = "points already given for today or the profile created is new"

            else:
                students = StudentProfile.objects.filter(user_id=user_id)
                for student in students:
                    created_date = student.created_at.date().strftime("%Y-%m-%d")

                    if created_date != today_date:
                        add_points_to_student(
                            point_activity="daily_open",
                            points=40, time=0,
                            user_id=user_id,
                            student_id=student.student_id,
                        )
                        # send daily open signal to event queue for milestone
                        # custom_signal_for_aws_queue.send(
                        #     sender="custom_daily_open",
                        #     instance={'student_id': student.student_id}
                        # )

                cache.set(key, user_id, datetime.timedelta(hours=23).total_seconds())
                response = "points added"

            return Response(
                {
                    "message": "success",
                    "status": status.HTTP_200_OK,
                    "response": response
                }
            )
        except Exception as err:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {err.__traceback__.tb_lineno}, Error: {err}"
                }
            )
          
    @action(methods=["get"], detail=False)
    def get_total_student_points(self, request, *args, **kwargs):
        try:
            data = request.query_params
            student_id = data.get('student_id')
            redis_key = f'total_points_{student_id}'
            data = student_total_points_sync.get_data(key=redis_key)
            if data:
                data = json.loads(data)
            else:
                data = {"student_id": student_id, "total_points": 0}

            return Response(
                {
                    "message": "success",
                    "status": status.HTTP_200_OK,
                    "response": data
                }
            )
        except Exception as err:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {err.__traceback__.tb_lineno}, Error: {err}"
                }
            )


class MilestonesViewSet(viewsets.ModelViewSet):
    queryset = Milestones.objects.all()
    serializer_class = MilestonesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ['is_deleted']
    filterset_class = MilestoneFilters
    search_fields = ['sn', 'title']
    ordering_fields = ['created_at', 'updated_at', 'sn', 'value']

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return Milestones.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    @action(methods=['get'], detail=True)
    def get_student_milestone(self, request, *args, **kwargs):
        student_id = kwargs.get('pk')

        # add filters
        filtered_queryset = self.filter_queryset(self.get_queryset())
        
        # add pagination
        paginator = LimitOffsetPagination()
        paginator.default_limit = 10
        paginator.offset = 0

        page = paginator.paginate_queryset(filtered_queryset, request)

        serializer = StudentMilestonesSerializer(page, context={'student_id': student_id}, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=True)
    def get_milestone(self, request, *args, **kwargs):
        student_id = kwargs.get('pk')
        class_id = request.query_params.get('class_id', None)
        medium_id = request.query_params.get('medium_id', None)
        result = []
        value = {}

        for milestone in MILESTONES_CHOICES:
            query = {}
            total_class_query = {}
            value['milestone'] = milestone[0]

            if milestone[0] == 'Total Chapter':
                query.update({'milestone__medium_id': medium_id})
                query.update({'milestone__class_id': class_id})
                total_class_query.update({'class_id': class_id})
                total_class_query.update({'medium_id': medium_id})

            value['total'] = Milestones.objects.filter(is_deleted__in=[False], milestone=milestone[0],
                                                       **total_class_query).count()
            value['completed'] = StudentMilestone.objects.filter(milestone__is_deleted__in=[False],
                                                student_id=student_id, milestone_type=milestone[0], **query).count()
            result.append(value)
            value = {}

        return Response(
            {
                "message": "success",
                "status": status.HTTP_200_OK,
                "response": result
            }, status=status.HTTP_200_OK
        )


class StudentMcqFirstAttemptViewSet(viewsets.ModelViewSet):
    queryset = McqFirstAttempt.objects.all()
    serializer_class = McqFirstAttemptSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    http_method_names = ['post']

    @action(detail=False, methods=['post'])
    def mcq_attempts(self, request, **kwargs):
        data = self.request.data
        part_id = data.get('part')
        student_id = data.get('student_id')
        attempt_no = McqFirstAttempt.objects.filter(part_id=part_id, student_id=student_id).count()
        data['attempt_no'] = attempt_no + 1
        attempt_serializer = self.get_serializer(data=data)

        if attempt_serializer.is_valid(raise_exception=True):
            attempt_serializer.save()

        objects = McqBestAttempt.objects.filter(part_id=part_id, student_id=student_id)

        if objects:
            mark = objects.first().marks
            if data.get('marks') > mark:
                objects.update(marks=data.get('marks'), status=data.get('status'))

            return Response(dict(message="Best Attempt record updated"),
                            status=status.HTTP_200_OK)
        else:
            best_attempt_serializer = McqBestAttemptSerializer(data=data)
            if best_attempt_serializer.is_valid():
                best_attempt_serializer.save()
                return Response(dict(message=attempt_serializer.data),
                                status=status.HTTP_201_CREATED)


class DiamondViewSet(viewsets.ModelViewSet):
    queryset = Diamond.objects.all()
    serializer_class = DiamondSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return Diamond.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    @action(methods=['get'], detail=True)
    def get_student_diamond(self, request, *args, **kwargs):
        try:
            student_id = kwargs.get('pk')
            redis_key = f'total_diamond_{student_id}'
            data = student_total_diamond_sync.get_data(key=redis_key)
            if data:
                data = json.loads(data)
            else:
                data = {"student_id": student_id, "total_diamond": 0}

            return Response(
                {
                    "message": "success",
                    "status": status.HTTP_200_OK,
                    "response": data
                }
            )
        except Exception as err:
            return Response(
                {
                    "message": "Failed",
                    "status": status.HTTP_400_BAD_REQUEST,
                    "response": f"Error on line {err.__traceback__.tb_lineno}, Error: {err}"
                }
            )


class DailyStreakViewSet(viewsets.ModelViewSet):
    queryset = DailyStreak.objects.all()
    serializer_class = DailyStreakSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [StudentPermission]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return DailyStreak.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    @action(methods=['post'], detail=True)
    def mark_daily_login(self, request, *args, **kwargs):
        """

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        user_id = self.request.user.user_id
        student_id = kwargs.get('pk')
        today = datetime.datetime.now().date()
        last_login = DailyStreak.objects.filter(student_id=student_id).last()
        data = {}

        if last_login and last_login.last_login_date != today:
            streak_count = last_login.streak_count + 1
        else:
            streak_count = 1

        try:
            reward = DailyReward.objects.get(reward_day=streak_count)
            data = {
                'streak_count': streak_count, 'point': reward.points,
                'diamond': reward.diamond, 'google_form_link': reward.google_form_link
            }
        except:
            reward = None

        DailyStreak.objects.get_or_create(
            student_id=student_id, last_login_date=today,
            defaults={"user_id": user_id, 'streak_count': streak_count, 'reward': reward},
        )

        return Response(
            {
                "message": "success",
                "status": status.HTTP_200_OK,
                "response": data
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def get_daily_streak(self,  request, *args, **kwargs):
        current_month = datetime.datetime.now().month
        month = self.request.query_params.get('month', current_month)
        student_id = kwargs.get('pk')
        current_year = datetime.datetime.now().year

        # Get the first and last day of the current month
        _, last_day_of_month = calendar.monthrange(current_year, month)
        first_day_of_month = datetime.datetime(current_year, current_month, 1)
        last_day_of_month = datetime.datetime(current_year, current_month, last_day_of_month)

        objects = DailyStreak.objects.filter(student_id=student_id, last_login_date__gte=first_day_of_month,
                                             last_login_date__lte=last_day_of_month).values('last_login_date')

        return Response(
            {
                "message": "success",
                "status": status.HTTP_200_OK,
                "response": objects
            },
            status=status.HTTP_200_OK
        )

    @action(methods=['get'], detail=True)
    def get_last_ten_records(self, request, *args, **kwargs):
        student_id = kwargs.get('pk')
        queryset = self.get_queryset().filter(student_id=student_id).order_by(
            '-last_login_date').values('last_login_date', 'streak_count')[0:10]

        data_count = queryset and queryset[0].get('streak_count') or 0
        result = queryset[0:data_count]
        return Response(
            {
                "message": "success",
                "status": status.HTTP_200_OK,
                "response": result
            },
            status=status.HTTP_200_OK
        )
