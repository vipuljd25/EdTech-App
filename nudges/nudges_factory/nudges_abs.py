import abc
import datetime
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from utils.common_methods import custom_mongo_client, logger
import json


class NudgesAbs(abc.ABC):
    def __init__(self, student_id, action, **kwargs):
        self.student_id = student_id
        self.action = action
        self.kwargs = kwargs
        self.student_profile_obj = self.set_student_profile(self.student_id)
        self.student_nudges_collection = custom_mongo_client.get_collection('nudges_studentnudges')

    @staticmethod
    def set_student_profile(student_id):
        collection = custom_mongo_client.get_collection('Students_App_studentprofile')
        student_profile_obj = collection.find_one({'student_id': student_id})
        return student_profile_obj

    def fetch_all_nudges(self, nudges_type):

        try:
            query = [
                {
                    '$match': {
                        'nudges_type': {'$in': nudges_type},
                        '$and': [
                            {
                                '$or': [
                                    {
                                        'state_id': self.student_profile_obj.get('student_state_id_id')
                                    }, {
                                        'state_id': None
                                    }
                                ]
                            }, {
                                '$or': [
                                    {
                                        'district_id': self.student_profile_obj.get('student_district_id_id')
                                    }, {
                                        'district_id': None
                                    }
                                ]
                            }, {
                                '$or': [
                                    {
                                        'block_id': self.student_profile_obj.get('student_block_id_id')
                                    }, {
                                        'block_id': None
                                    }
                                ]
                            }, {
                                '$or': [
                                    {
                                        'school_id': {'$in': [self.student_profile_obj.get('school_id_id')]}
                                    }, {
                                        'school_id': []
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]

            nudges_collection = custom_mongo_client.get_collection('nudges_nudges')
            result = nudges_collection.aggregate(query)
            all_nudges = list(result)
            return all_nudges

        except Exception as err:
            logger.log_error(f"Nudges-> error in function fetch_all_nudges, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def is_flagged(self, nudges):

        try:
            # Check if data already exists
            criteria = {
                "student_id": self.student_id,
                "nudges_id": nudges.get('_id'),
            }
            existing_data = self.student_nudges_collection.find_one(criteria)
            return existing_data

        except Exception as err:
            logger.log_error(f"Nudges-> error in function check_if_exists, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    @abc.abstractmethod
    def is_satisfy_condition(self, nudges):
        raise NotImplementedError

    @staticmethod
    def find_next_sent_date(wait_duration):
        """
        wait duration is in days
        """
        current_time = datetime.datetime.utcnow()
        next_sent_at = current_time + datetime.timedelta(days=wait_duration)
        return next_sent_at

    def set_student_nudges(self, nudges):

        wait_duration = nudges.get('timeframe_duration')
        nudge_id = nudges.get('_id')

        data_to_insert = {
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow(),
            "student_id": self.student_id,
            "user_id": self.student_profile_obj.get("user_id_id"),
            "nudges_id": nudge_id,
            "last_sent_at": None,
            "next_sent_at": self.find_next_sent_date(wait_duration),
            "active": True,
        }
        # Insert the data
        student_nudge = self.student_nudges_collection.insert_one(data_to_insert)
        logger.log_info(f"Nudges-> Flagged student: {self.student_id} for nudge_id: {nudge_id}")
        return student_nudge

    @abc.abstractmethod
    def process_nudges(self):
        raise NotImplementedError

    def scheduled_task(self, nudges, student_nudge):
        pass
        # arg = json.dumps([self.student_id, self.action, str(student_nudge.inserted_id)])
        # start_time = datetime.datetime.utcnow() + datetime.timedelta(days=nudges.get('time_duration'))
        # kwargs = json.dumps(self.kwargs)
        # interval_obj, created = IntervalSchedule.objects.get_or_create(
        #     every=nudges.get('repeat_time_duration'),
        #     defaults={"period": "days"},
        # )
        # repeat = False
        # if nudges.get('repeat'):
        #     repeat = True
        # obj = {
        #       "name": str(student_nudge.inserted_id),
        #       "task": "nudges.tasks.sent_nudges",
        #       "interval_id": interval_obj.id,
        #       "args": arg,
        #       "kwargs": kwargs,
        #       "one_off": repeat,
        #       "start_time": start_time,
        #     }
        # PeriodicTask.objects.create(**obj)

    @abc.abstractmethod
    def decision_maker(self, nudge, student_nudge):
        raise NotImplementedError

    @abc.abstractmethod
    def get_template_variables(self, nudge_data, student_nudge_data):
        pass

