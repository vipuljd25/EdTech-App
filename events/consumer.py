import boto3
import os
from events.tasks import process_sqs_message
from student_activity.settings import (AWS_S3_REGION_NAME,
                                       AWS_ACCESS_KEY_ID,
                                       AWS_SECRET_ACCESS_KEY)


def consume_sqs_messages():
    sqs = boto3.client('sqs',
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=AWS_S3_REGION_NAME)
    queue_url = os.environ['EVENTS_QUEUE']

    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            MessageAttributeNames=['All'],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        messages = response.get('Messages', [])

        for message in messages:
            message_body = message['Body']
            receipt_handle = message['ReceiptHandle']

            # Call Celery task to process the message asynchronously
            process_sqs_message.delay(message_body)

            # Delete the message from the queue
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
