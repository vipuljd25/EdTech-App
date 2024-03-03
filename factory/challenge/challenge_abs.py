import abc
from utils.common_methods import custom_mongo_client
from factory.constance import CHALLENGES, SUB_CHALLENGES, EVENTS_MODEL
from factory.calculation.factory import CalculationFactory
from factory.notification.notification_factory import NotificationFactory
from factory.notification.mongo_query import device_token_from_studentchallengedata


class ChallengeAbs(abc.ABC):
    def __init__(self, action, student_id, **kwargs):
        self.action_from_model = EVENTS_MODEL[action]
        self.action = self.action_from_model
        self.student_id = student_id
        self.kwargs = kwargs
        self.student_challenge_collection = custom_mongo_client.get_collection('challenges_studentchallengedata')
        self.sub_challenges = SUB_CHALLENGES[CHALLENGES[self.action]]
        self.challenges = []
        self.get_accepted_and_active_challenge()
        self.unset_progress_array = ['AI Reels In One Session', 'Teacher Generated In One Session']

    def get_accepted_and_active_challenge(self):
        """
        Method will use for getting all available active and accepted challenge
        for a given student.
        :return: django queryset
        """

        self.challenges = self.student_challenge_collection.aggregate(
            [
                {'$match': {
                    'status': 'ACCEPTED',
                    'challenge_status': 'ACTIVE',
                    'student_id': self.student_id
                }},
                {'$lookup': {
                    'from': 'challenges_challengedata',
                    'localField': 'challenge_id',
                    'foreignField': '_id',
                    'as': 'challenges_data'
                }},
                {'$unwind': {
                    'path': '$challenges_data',
                    'preserveNullAndEmptyArrays': False
                }},
                {'$replaceRoot': {
                    'newRoot': '$challenges_data'
                }},
                {'$match': {
                    'challenge_info.sub_challenge':
                        {'$in': self.sub_challenges}

                }}
            ])

    @staticmethod
    def get_calculation_instance(student_id, challenge_obj, **kwargs):
        """
        Method is used for getting instance of the calculation.
        :return: instance
        """
        challenge_info = challenge_obj.get('challenge_info')
        calculation = challenge_info.get('sub_challenge').replace(" ", "")

        instance = CalculationFactory(student_id, calculation, **kwargs).create_instance()
        return instance

    @abc.abstractmethod
    def is_challenge_completed(self, calculating_instance, challenge_info, student_challenge_obj):
        raise NotImplementedError

    @staticmethod
    def get_device_token(student_challenge_obj):
        notification_data = {
            '_id': student_challenge_obj._id
        }
        query = device_token_from_studentchallengedata(**notification_data)
        collection = custom_mongo_client.get_collection('challenges_studentchallengedata')
        device_token_list = collection.aggregate(query)
        token_list = [item['token'] for item in list(device_token_list)]  # TODO optimize
        return token_list

    @staticmethod
    def get_notification_instance(platform, **kwargs):
        instance = NotificationFactory(platform=platform, **kwargs).notification_instance
        return instance

    @abc.abstractmethod
    def mark_challenge_completed(self, challenge):
        raise NotImplementedError

    @abc.abstractmethod
    def sent_completed_notification(self, challenge, student_challenge_obj):
        raise NotImplementedError

    @abc.abstractmethod
    def check_challenge_completed(self):
        """
        Method for compair value to check challenge completed or not
        and set in challenge_completed variable.
        :return:
        """
        raise NotImplementedError
