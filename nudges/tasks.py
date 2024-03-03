import datetime
import re

from bson import ObjectId
from celery import shared_task

from factory.notification.notification_factory import NotificationFactory
from nudges.models import StudentNudges, Nudges
from nudges.nudges_factory.nudges_factory import NudgesFactory
from utils.common_methods import logger, custom_mongo_client


def get_variables_by_template_id(template_id):
    collection = custom_mongo_client.get_collection('nudges_templates')
    template_obj = collection.find_one({"_id": template_id})
    template_variables = template_obj.get('variables')
    template_name = template_obj.get('template_name')
    language = template_obj.get('language')
    return template_variables, template_name, language


def get_device_token(user_id):
    collection = custom_mongo_client.get_collection('Students_App_devices')
    device_obj = collection.find_one({"user_id": user_id})
    token = device_obj.get('token')
    return [token]


def send_nudge_in_whatsapp(nudge_data, variables):
    # get whatsapp variables from template model
    template_id = nudge_data.get('template')
    wp_variables_list, wp_template_name, language = get_variables_by_template_id(template_id)

    parameter = []
    for key, value in variables.items():
        if key in wp_variables_list:
            data = {'type': "text", 'text': value}
            parameter.append(data)

    notification_instance = NotificationFactory(platform="WhatsAppNotification", **{})
    notification_instance.notification_instance.send_notification(parameter, phone_no=10,
                                                                  template_name="a", language=language)


def send_nudge_in_drawer(nudge_data, variables, student_nudge_data):
    message = nudge_data.get('message')
    in_app_variable_list = re.findall(r'{(.*?)}', message)

    if not in_app_variable_list:
        logger.log_error(f"Nudges-> func: send_nudges -> InAppNotification -> No variables found in message"
                         f"nudge_id = {nudge_data.get('_id')}")

    for i in in_app_variable_list:
        message = message.replace(f'{{{i}}}', str(variables[i]))

    device_token_list = get_device_token(student_nudge_data.get('user_id'))

    notification_instance = NotificationFactory(platform="InAppNotification", **{})
    notification_instance.notification_instance.send_notification(
        heading="nudge",  # TODO what heading?
        content=message,
        image_url="",
        device_token_list=device_token_list,
        data={},
        in_app=False
    )


def update_nudge(student_nudge_data, query=None, force_stop=True):
    # force disable a student nudge

    if force_stop and query is None:
        query = {"next_send_at": None, "active": False}

    if force_stop:
        celery_collection = custom_mongo_client.get_collection('django_celery_beat_periodictask')
        celery_collection.update_one(
            {"name": str(student_nudge_data.get('_id'))},
            {"$set": {"enable": False}}
        )

    student_nudges_collection = custom_mongo_client.get_collection('nudges_studentnudges')
    student_nudges_collection.update_one(
        {"_id": student_nudge_data.get('_id')},
        {"$set": query}
    )
    pass


@shared_task
def sent_nudges(nudge_type, student_nudge_id, **kwargs):

    student_nudge_data = StudentNudges.objects.filter(_id=ObjectId(student_nudge_id)).values().first()
    student_id = student_nudge_data.get('student_id')

    nudge_data = Nudges.objects.filter(_id=student_nudge_data.get('nudges_id')).values().first()
    is_satisfy_condition = NudgesFactory(student_id, nudge_type,
                                         **kwargs).nudges_instance.decision_maker(nudge_data, student_nudge_data)

    if is_satisfy_condition:
        variables = NudgesFactory(student_id, nudge_type, **kwargs).nudges_instance.get_template_variables(nudge_data)

        if nudge_data.get('notification_platform') == "WhatsApp":
            send_nudge_in_whatsapp(nudge_data, variables)

        if nudge_data.get('notification_platform') == "Drawer":
            send_nudge_in_drawer(nudge_data, variables, student_nudge_data)

    query = {}
    if nudge_data.get('repeat'):
        # update student nudges and increment sent_count
        new_sent_count = student_nudge_data.get('sent_count') + 1
        query.update(
            {
                "sent_count": new_sent_count,
                "last_sent_at": datetime.datetime.utcnow(),
                "next_sent_at": datetime.datetime.utcnow() + datetime.timedelta(days=nudge_data.get('repeat_time_duration'))
            }
        )
        if nudge_data.get('repeat_count') == new_sent_count:
            # turn off nudge
            update_nudge(student_nudge_data, force_stop=True)

    else:
        # disable_nudge -> celery will turn off automatically
        query.update({"next_sent_at": None})

    # using query to update student_nudges_table
    update_nudge(student_nudge_data, query=query, force_stop=False)



