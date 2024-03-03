import datetime
import os
from datetime import timedelta

from student_activity import settings
import boto3
from pymongo import MongoClient

aws_s3_client = boto3.client(
     's3',
     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
     region_name=settings.AWS_S3_REGION_NAME
)


def field_validation(*req_fields, **data):
    """
    Method is used in the validation for
    the required fields.
    :param req_fields:
    :param data:
    :return:
    """
    req_fields = set(req_fields)
    received = set(data.keys())
    missing = req_fields.difference(received)
    return missing


def upload_file_on_s3(file, file_path, file_type, content_type = "text"):
    """
    Method is used to upload the image on the given key(path).
    ContentType---examples
        text/plain: Plain text files.
        text/html: HTML files.
        application/json: JSON data.
        application/xml: XML data.
        image/jpeg, image/png, etc.: Various image formats.
        audio/mpeg, audio/wav, etc.: Various audio formats.
        video/mp4, video/quicktime, etc.: Various video formats.
    """
  
    content = f'{content_type}/{file_type}'

    _ = aws_s3_client.put_object(
        Body=file, ContentType=content, Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_path, ACL='public-read'
    )
    file_url = settings.CDN_URL + file_path
    return file_url


def get_start_end_dates(flag, filter_dates=True):
    """
    This function is used to get the start_date or end_date of the last week, month, quarter, or half-year
    based on flag and the current date.
    """
    # Get the current date
    start_date = datetime.datetime.now()

    if flag == '1 Month':
        # Calculate the start date of the last month
        # Calculate the end date of the last month by moving to the current month's start and subtracting a day
        end_date = start_date - timedelta(days=30)

    elif flag == 'Week':
        # Calculate the start date of the last week (Monday)
        # Calculate the end date of the last week (Sunday)
        end_date = start_date - timedelta(weeks=1)

    elif flag == '2 Month':

        end_date = start_date - timedelta(weeks=8)

    elif flag == '3 Month':
        end_date = start_date - timedelta(weeks=12)

    elif flag == '6 Month':
        # Calculate the start date of the last half-year
        end_date = start_date - timedelta(weeks=24)

    else:
        return "Invalid flag. Please use 'month', 'week', 'quarter', or 'half_year'."
    if filter_dates:
        return {'$and': [{'created_at': {'$gte': end_date}}]}
    return end_date


def get_operator(string_operator):
    if string_operator == 'more':
        return '$gt'
    if string_operator == 'equal':
        return '$eq'
    if string_operator == 'less':
        return '$lt'


from rest_framework.views import exception_handler as drf_exception_handler
from utils.common_methods import logger


def custom_exception_handler(exc, context):
    # Log the exception
    logger.error(f"An error occurred: {str(exc)}")

    # Call the default exception handler for additional processing
    response = drf_exception_handler(exc, context)

    if response is None:
        # Handle unhandled exceptions (internal server errors)
        response = Response({'detail': 'Internal Server Error'}, status=500)

    return response


def get_end_date(timeframe, start_date):
    # TODO change in db for time frame for Reels
    if timeframe == 'Day':
        end_date = start_date + timedelta(days=1)
    elif timeframe == 'Week':
        end_date = start_date + timedelta(weeks=1)
    elif timeframe == 'Month':
        # Note: This method does not precisely handle months with varying numbers of days
        end_date = start_date + timedelta(days=30)  # Assuming a month is approximately 30 days
    elif timeframe == 'Quarter':
        end_date = start_date + timedelta(days=90)  # Assuming a quarter is approximately 90 days
    elif timeframe == 'Half Year':
        end_date = start_date + timedelta(days=180)  # Assuming half a year is approximately 180 days
    else:
        raise ValueError("Invalid time frame")

    return end_date
