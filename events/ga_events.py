from requests import request
import json
import time
from student_activity import settings

url = f"https://google-analytics.com/mp/collect?api_secret={settings.api_secret}&firebase_app_id={settings.firebase_app_id}"


def send_ga_event(event_name, user_time,  **events_details):
    payload = json.dumps({
      "app_instance_id": settings.app_instance_id,
      "user_id": user_time,
      "timestamp_micros": str(time.time_ns()),
      "non_personalized_ads": False,
      "events": [
        {
          "name": event_name,
          "params": {
            "items": [
              {
                "item_id": "",
                "item_name": "challenge_item_name",
                "affiliation": "",
                "coupon": "",
                "currency": "",
                "discount": 0,
                "index": 0,
                "item_brand": "",
                "item_category": "",
                "item_category2": "",
                "item_category3": "",
                "item_category4": "",
                "item_category5": "",
                "item_list_id": "",
                "item_list_name": "",
                "item_variant": "",
                "location_id": "",
                "price": 0,
                "quantity": 0,
                "creative_name": "",
                "creative_slot": "",
                "promotion_id": "",
                "promotion_name": ""
              }
            ],
            **events_details
            # "student_id": "123456",
            # "challenge_complete": "yes"
          }
        }
      ],
      "validationBehavior": "ENFORCE_RECOMMENDATIONS"
    })

    headers = {
      'Content-Type': 'application/json'
    }

    response = request("POST", url, headers=headers, data=payload)
