import json
import os
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver, Signal
from django.apps import apps
from data_points.models import PartsProgress, McqBestAttempt, ReelsAttempt, \
    StudentElementTime, StudentTimePoints, Milestones, ChapterProgress, ChapterParts, McqFirstAttempt, Diamond
from data_points.serializers import ChapterProgressSerializer
from student_activity.redis_sync import student_total_points_sync, student_total_diamond_sync
from utils.common_methods import SQSPublisher, custom_mongo_client
from utils.common_methods import logger

custom_signal_for_aws_queue = Signal()  # signal used to send messages to aws queue only for custom actions
event_models = [
    PartsProgress, McqFirstAttempt, ReelsAttempt,
    StudentElementTime, StudentTimePoints
]


# Producer of event messages in queue.
@receiver(post_save, sender=McqFirstAttempt)
@receiver(post_save, sender=ReelsAttempt)
@receiver(post_save, sender=StudentElementTime)
@receiver(post_save, sender=StudentTimePoints)
def events_handler(sender, instance, **kwargs):
    removed_fields = ['_id', '_state', 'created_at', 'updated_at']
    try:
        if sender in event_models:
            queue_url = os.environ['EVENTS_QUEUE']
            values = instance.__dict__
            message = {
                'action': sender.__name__, **values
            }
            [message.pop(i, None) for i in removed_fields]
            message_body = json.dumps(message)
            sqs_obj = SQSPublisher(queue_url, message_body)
            sqs_obj.publish_sqs_msg()
        logger.log_info(f'Data is sent to queue for {sender.__name__}')
    except Exception as e:
        logger.log_error('events_handler -> Error while sending message in queue')


@receiver(pre_save, sender=Milestones)
def set_serial_number(sender, instance, **kwargs):
    if not instance.sn:
        latest_serial_number = Milestones.objects.order_by('-sn').first()
        if latest_serial_number:
            instance.sn = latest_serial_number.sn + 1
        else:
            instance.sn = 1


def update_chapter_progress(sender, instance):
    if sender == "PartsProgress":
        chapter_id = instance.get('chapter_id')
        student_id = instance.get('student_id')
        part_obj = ChapterParts.objects.filter(chapter_id=chapter_id, is_deleted__in=[False])
        no_of_parts = len(part_obj)

        chapter_percentage = 0
        chapter_time = 0
        chapter_points = 0

        for obj in part_obj:
            progress_obj = PartsProgress.objects.filter(part_id=obj.part_id, student_id=student_id).first()
            if progress_obj:
                chapter_percentage += progress_obj.percentage
                chapter_time += progress_obj.time
                chapter_points += progress_obj.points

        chapter_percentage = chapter_percentage / no_of_parts
        chapter_percentage = round(chapter_percentage, 2)

        chapter_progress_instance = ChapterProgress.objects.filter(
            user_id=instance.get('user_id'), student_id=student_id,
            chapter_id=chapter_id, subject_id=instance.get('subject_id')).first()
        # data to save in chapter_progress
        chapter_progress_data = {
            "user_id": instance.get('user_id'), "student_id": student_id, "chapter_id": chapter_id,
            "subject_id": instance.get('subject_id'), "class_id": instance.get('class_id'),
            "percentage": chapter_percentage,
            "points": chapter_points, "time": chapter_time
        }

        # if instance update data and if instance = none then create data
        serializer = ChapterProgressSerializer(chapter_progress_instance, data=chapter_progress_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()


@receiver(post_save, sender=StudentTimePoints)
def calculate_total_points(sender, instance, **kwargs):
    student_id = instance.student_id
    new_point = instance.points
    redis_key = f'total_points_{student_id}'
    data = student_total_points_sync.get_data(key=redis_key)
    if data:
        data = json.loads(data)
        data["total_points"] = data["total_points"] + new_point
    else:
        # aggregate
        query = [
            {'$match': {'student_id': student_id}},
            {'$group': {'_id': '$student_id', 'total_points': {'$sum': '$points'}}}
        ]
        collection = custom_mongo_client.get_collection('data_points_studenttimepoints')
        aggregate_data = list(collection.aggregate(query))
        total_points = aggregate_data[0].get("total_points")
        data = {"student_id": student_id, "total_points": total_points}

    redis_data = json.dumps(data)
    student_total_points_sync.upload_data(key=redis_key, value=redis_data)


@receiver(post_save, sender=Diamond)
def calculate_total_diamond(sender, instance, **kwargs):
    student_id = instance.student_id
    diamond = instance.diamond
    redis_key = f'total_diamond_{student_id}'
    data = student_total_diamond_sync.get_data(key=redis_key)
    if data:
        data = json.loads(data)
        data["total_diamond"] = data["total_diamond"] + diamond
    else:
        # aggregate
        query = [
            {'$match': {'student_id': student_id}},
            {'$group': {'_id': '$student_id', 'total_diamond': {'$sum': '$diamond'}}}
        ]
        collection = custom_mongo_client.get_collection('data_points_diamond')
        aggregate_data = list(collection.aggregate(query))
        diamond = aggregate_data[0].get("total_diamond", 0)
        data = {"student_id": student_id, "total_diamond": diamond}

    redis_data = json.dumps(data)
    student_total_diamond_sync.upload_data(key=redis_key, value=redis_data)


@receiver(custom_signal_for_aws_queue)
def events_handler_for_custom_signals(sender, instance, **kwargs):
    try:
        queue_url = os.environ['EVENTS_QUEUE']
        values = instance
        message = {
            'action': sender, **values
        }
        message_body = json.dumps(message)
        sqs_obj = SQSPublisher(queue_url, message_body)
        sqs_obj.publish_sqs_msg()
        logger.log_info(f'Data is sent to queue for {sender}')
        if sender == "PartsProgress":
            update_chapter_progress(sender, instance)
    except Exception as e:
        logger.log_error(f'custom_signal_error -> Error while sending message in queue, Error: {e}')
