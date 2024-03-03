import uuid
import requests

from factory.notification.notification_abs import NotificationAbs
from firebase_admin import messaging
from student_activity.settings import WHATS_APP_TOKEN, WHATS_APP_URL


class InAppNotification(NotificationAbs):

    @staticmethod
    def send_notification(heading, content, image_url, device_token_list, data, in_app=True):
        """
        send In App notification to students
        target_kwargs = data needed to filter out user_device_token_list from device collection
        """
        # create topic if user_token is more than 500
        topic_name = f"STUDENT_CHALLENGE_{uuid.uuid4()}"
        if len(device_token_list) > 500:
            chunk_size = 1000
            messaging_topic = []
            for tokens in range(0, len(device_token_list), chunk_size):
                chunks = device_token_list[tokens:tokens + chunk_size]
                messaging_topic = messaging.subscribe_to_topic(chunks, topic_name)
            sender_kwargs = {
                "topic": messaging_topic
            }
        else:
            sender_kwargs = {
                "tokens": device_token_list
            }
        in_mobile_notification = dict(
                notification=messaging.Notification(
                    title=heading,
                    body=content,
                    image=image_url
                ),

                android=messaging.AndroidConfig(
                    # ttl=datetime.timedelta(days=28),
                    priority='normal',
                    # data={"global_notification": notification_flag, "url": url[0]},
                    notification=messaging.AndroidNotification(
                        icon='https://iconarchive.com/download/i58917/wwalczyszyn/android-style-honeycomb/Books.ico',
                        color='#f45342',
                        body_loc_key='version'
                    ),
                ),

                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(badge=42),
                    ),
                ),
        )
        if not in_app:
            in_mobile_notification = {}
        message = messaging.MulticastMessage(
            data=data,
            **in_mobile_notification,
            **sender_kwargs,
        )
        response = messaging.send_multicast(message)


class WhatsAppNotification(NotificationAbs):
    """
    send WhatsApp notification to students
    """

    @staticmethod
    def send_notification(variables, phone_no, template_name, language):

        url = WHATS_APP_URL
        headers = {
            "Authorization": WHATS_APP_TOKEN,
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": phone_no,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": variables
                    }
                ]
            }
        }

        response = requests.post(url, json=data, headers=headers)


# class SmsNotification(NotificationAbs):
#     """
#     send SMS notification to students
#     """
#
#     def send_notification(self, heading, content, image_url, user_id_list):
#         pass
#
