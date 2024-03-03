import json
import logging
import os
import json
import datetime

from celery import shared_task
from django.core.cache import cache

from data_points.models import Chapter
from factory.challenge.factory import ChallengeFactory
from factory.milestone.milestone_factory import MilestoneFactory
from nudges.nudges_factory.nudges_factory import NudgesFactory
from utils.common_methods import SNSPublisher
from factory.constance import EVENTS_MODEL, MILESTONES
logger = logging.getLogger(__name__)
SNS_ARN = os.environ['ERROR_SNS_ARN']
ENV = os.environ.get('env') or 'development'


@shared_task
def process_sqs_message(message_body):
    message_body = json.loads(message_body)
    action = message_body.pop('action')
    student_id = message_body.pop('student_id')
    try:
        # handel action for Challenges
        if action in list(EVENTS_MODEL.keys()):
            ChallengeFactory(action=action, student_id=student_id, **message_body)
            logger.info(f'Challenge check -> {action} for a student id {student_id}')

        # handel action for Milestone
        if action in list(MILESTONES.keys()):
            MilestoneFactory(action=action, student_id=student_id, **message_body)
            logger.info(f'Milestone check -> {action} for a student id {student_id}, kwargs: {message_body}')

        # handel action for Nudges
        if action in ["ChapterProgress", "ReelsAttempt", "Challenges", "Milestone", "McqFirstAttempt"]:

            action_list = list(action)
            if action == "ChapterProgress":
                sc_chapter_id = message_body.get('subject_id')
                special_course_subject_list = cache.get("special_course_subject_list")

                # if list not found in cache call db
                if not special_course_subject_list:
                    special_course_subject_list = Chapter.objects.filter(district_id_id=7).values_list(
                        'subject_id_id', flat=True).distinct()
                    key = "special_course_subject_list"
                    cache.set(key, special_course_subject_list, datetime.timedelta(days=1))

                if sc_chapter_id in special_course_subject_list:
                    # if subject is special course overwrite action
                    action_list = ["SpecialCourseProgress"]
                    pass

            if action == "ReelsAttempt":
                # separate KnowledgeReels, AIGeneratedReelsOnTopic, TotalReels from ReelsAttempt
                ai_generated = message_body.get('ai_generated')
                if ai_generated:
                    action_list = ["TotalReels", "AIGeneratedReelsOnTopic", "KnowledgeReels"]
                else:
                    action_list = ["TotalReels", "KnowledgeReels"]

            for action in action_list:
                try:
                    NudgesFactory(action=action, student_id=student_id, **message_body).nudges_instance.process_nudges()
                    logger.info(f'nudges_flag -> call process_nudges for Nudge = {action} for student_id {student_id}')
                except Exception as err:
                    logger.error(f"nudges_flag -> Function: process_sqs_message, "
                                 f"Details: Error while calling process_nudges method, Error: {str(err)}")

    except Exception as err:
        subject = 'Error in Challenge Tracking'
        message = {'environment': ENV, 'error': str(err), 'action': action, 'student_id': student_id}
        SNSPublisher(SNS_ARN, message, subject).publish_notification_email()
        logger.error({'error': err, 'function_name': 'ChallengeFactory class'})
