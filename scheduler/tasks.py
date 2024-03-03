import datetime
import logging
import os
from utils.common_methods import custom_mongo_client, is_datetime_in_range
from challenges.models import StudentChallengeData, ChallengeData
from celery import shared_task
from factory.notification.notification_factory import NotificationFactory
from factory.notification.mongo_query import device_token_from_studentchallengedata
from pymongo import InsertOne
from factory.calculation.factory import CalculationFactory

logger = logging.getLogger(__name__)


def get_task_progress(student_id, challenge_task, **kwargs):
    try:
        unit_key = kwargs.get('unit_key').replace(" ", "")
        unit_value = kwargs.get('unit_value')
        percentage = 0
        if unit_key == 'Minute':
            unit_value = unit_value * 60000
        if challenge_task not in ['Earn Points', 'Lesson Component',
                                  'AI Reels In One Session', 'Teacher Generated In One Session']:
            challenge_task = challenge_task.replace(' ', '')
            instance = CalculationFactory(student_id=student_id, calculation=challenge_task, **kwargs).create_instance()
            result = instance.calculate()
            if result:
                current_value = result[0].get(unit_key)
                percentage = current_value * 100 / unit_value
                percentage = percentage if percentage < 100 else 100
        return percentage
    except Exception as err:
        logger.error(f'error in progress calculation {err}')
        return 0


def set_student_records(challenge):
    try:
        # variables
        filter_condition = challenge['filter_condition']
        advance_filter_condition = challenge['advance_filter_condition']
        ad_filter = challenge['advance_filter']
        challenge_info = challenge['challenge_info']
        challenge_info.pop('challenge')
        challenge_task = challenge_info['sub_challenge']
        unit_value = challenge_info['unit_value']

        # collections
        student_data = custom_mongo_client.get_collection('data_points_studenttimepoints')
        student_challenge_data = custom_mongo_client.get_collection('Students_App_studentprofile')
        student_challenge = custom_mongo_client.get_collection('challenges_studentchallengedata')

        if advance_filter_condition and not ad_filter.get('user_type') == "Inactive User":
            target_students = student_data.aggregate(advance_filter_condition)
        elif advance_filter_condition and ad_filter.get('user_type') == "Inactive User":
            target_students = student_challenge_data.aggregate(advance_filter_condition)
        else:
            target_students = student_challenge_data.aggregate([{'$match': filter_condition}])
        target_students_array = []

        # send challenge to target students
        for students in target_students:

            progress = get_task_progress(student_id=students['student_id'], challenge_task=challenge_task,
                                         **challenge_info)

            student_challenge_data = {
                'created_at': datetime.datetime.utcnow(),
                'updated_at': datetime.datetime.utcnow(),
                'status': 'SENT',
                'challenge_status': 'ACTIVE',
                'user_id': students['user_id_id'],
                'student_id': students['student_id'],
                'challenge_id': challenge['_id'],
                'progress': progress
            }

            # check progress
            if progress != 100:
                target_students_array.append(InsertOne(student_challenge_data))

            if len(target_students_array) == 10000:
                student_challenge.bulk_write(target_students_array)
                target_students_array = []
        student_challenge.bulk_write(target_students_array)

    except Exception as err:
        logger.error({'error': err, 'function_name': 'set_student_records'})


def send_in_app_notification(challenge_obj):
    try:
        # TODO add multi threading
        if challenge_obj and os.environ.get('SEND_CHALLENGES_NOTIFICATION', True):
            #  get user_device_tokens
            notification_data = {"challenge_id": challenge_obj.get('_id')}
            query = device_token_from_studentchallengedata(**notification_data)
            collection = custom_mongo_client.get_collection('challenges_studentchallengedata')
            device_tokens = collection.aggregate(query)

            device_token_list = [item['token'] for item in list(device_tokens)]  # TODO optimize
            device_token_list = list(set(device_token_list))
            # create an instance of InApp notification class
            notification_instance = NotificationFactory(platform="InAppNotification")
            # call send_notification method from InApp notification class
            challenge_display = challenge_obj.get('challenge_display')
            data = {}
            notification_instance.notification_instance.send_notification(
                heading=challenge_display.get('display_sub_title'),
                content=challenge_display.get('display_description'),
                image_url=challenge_display.get('display_image'),
                device_token_list=device_token_list,
                data=data
            )
    except Exception as err:
        logger.error({'error': err, 'function_name': 'send_in_app_notification() in tasks.py'})


@shared_task
def update_challenge_status():
    try:
        logger.info('Challenge Published And Active Task Check running.')
        challenge = custom_mongo_client.get_collection('challenges_challengedata')
        student_challenge = custom_mongo_client.get_collection('challenges_studentchallengedata')
        published_data_obj = challenge.find({'status': {'$in': ['PUBLISHED', 'ACTIVE']}})
        for challenge_obj in published_data_obj:
            start_date = challenge_obj['start_date']
            end_date = challenge_obj['end_date']
            try:
                if is_datetime_in_range(start_date) and challenge_obj['status'] == 'PUBLISHED':
                    logger.info(f"{str(challenge_obj['_id'])} Challenge mark ACTIVE")

                    challenge.update({'_id': challenge_obj['_id']}, {'$set': {'status': 'ACTIVE'}})
                    set_student_records(challenge_obj)

                    # send InAppNotification for when challenges are sent to students
                    send_in_app_notification(challenge_obj)

                if is_datetime_in_range(end_date) and challenge_obj['status'] == 'ACTIVE':
                    logger.info(f"Challenge id {str(challenge_obj['_id'])} Mark EXPIRED", )
                    challenge.update({'_id': challenge_obj['_id']}, {'$set': {'status': 'EXPIRED'}})
                    # Change challenge status to expire for all students with this challenge
                    student_challenge.update_many({'challenge_id': challenge_obj['_id']},
                                                  {'$set': {'challenge_status': 'EXPIRED'}})

            except Exception as e:
                logger.error({'error': e,
                              'function_name': 'update_challenge_status',
                              'challenge_id': str(challenge_obj['_id'])}
                             )
    except Exception as err:
        logger.error({'error': err, 'function_name': 'update_challenge_status'})
        # -TODO-record log
