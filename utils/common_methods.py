import os
import datetime
import logging
import operator
import json
from rest_framework.views import exception_handler
from pymongo import MongoClient
import boto3
from student_activity.settings import (AWS_S3_REGION_NAME,
                                       AWS_ACCESS_KEY_ID,
                                       AWS_SECRET_ACCESS_KEY)


class CustomMongoSetup:
    def __init__(self, url=None, db=None):
        self.client_url = url or os.environ.get('MONGO_HOST')
        self.db_string = db or os.environ.get('MONGO_DB')
        self._client = None
        self.db = None

    def connect(self):
        if self._client is None:
            self._client = self._create_client()
            self.db = self._select_db()

    def _create_client(self):
        client = MongoClient(self.client_url)
        return client

    def _select_db(self):
        return self._client[self.db_string]

    def get_collection(self, collection):
        if self._client is None:
            self.connect()
        return self.db[collection]

    @property
    def client(self):
        if self._client is None:
            self.connect()
        return self._client


custom_mongo_client = CustomMongoSetup()


def is_datetime_in_range(date):
    current_datetime = datetime.datetime.utcnow()
    return date <= current_datetime


def perform_comparison(value, current_value, comparison_operator):
    operators = {
        'More': operator.gt,
        'Less': operator.lt,
        'Equal': operator.ge,
    }

    if comparison_operator not in operators:
        raise ValueError("Invalid comparison operator")

    return operators[comparison_operator](current_value, value)


class EnhancedApiLogger:
    def __init__(self, logger_name='api_logger'):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

    def log_info(self, message):
        self.logger.info(message)

    def log_error(self, message):
        self.logger.error(message)


class LoggingMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = EnhancedApiLogger()

    def log_info(self, message):
        user = getattr(self.request.user, 'user_id', 'Anonymous')
        method = self.request.method
        function_name = self.__class__.__name__
        action = self.action
        log_message = f"INFO -> User Id {user} Accessed {method} in {function_name} -> {action} - {message}"
        self.logger.log_info(log_message)

    def log_error(self, message=None):
        user = getattr(self.request.user, 'user_id', 'Anonymous')
        method = self.request.method
        function_name = self.__class__.__name__
        log_message = f"{user} encountered an error in {method} {function_name} - {message}"
        self.logger.log_error(log_message)


logger = EnhancedApiLogger()


class SQSPublisher:
    def __init__(self, queue_name, msg_body):
        self.queue_name = queue_name
        self.msg_body = msg_body

    @staticmethod
    def get_sqs_client():
        # Create SQS client
        sqs = boto3.client('sqs',
                           aws_access_key_id=AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                           region_name=AWS_S3_REGION_NAME)
        return sqs

    def publish_sqs_msg(self):
        sqs = self.get_sqs_client()
        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=self.queue_name,
            MessageBody=self.msg_body
        )


class SNSPublisher:
    def __init__(self, topic_arn, msg_body, subject):
        self.topic_arn = topic_arn
        self.msg_body = msg_body
        self.subject = subject

    @staticmethod
    def get_sqs_client():
        # Create SQS client
        sqs = boto3.client('sns',
                           aws_access_key_id=AWS_ACCESS_KEY_ID,
                           aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                           region_name=AWS_S3_REGION_NAME)
        return sqs

    def publish_notification_email(self):
        # Publish to topic
        sns = self.get_sqs_client()
        body = dict(
            default="Student Activity Notification",
            email=json.dumps(self.msg_body
                             )
        )
        final_message = json.dumps(body)
        sns.publish(
            TopicArn=self.topic_arn,
            Message=final_message,
            Subject=self.subject,
            MessageStructure='json'
        )
