import abc
import datetime

from data_points.utils import add_points_to_student, add_diamond_to_user
from factory.notification.notification_factory import NotificationFactory
from utils.common_methods import custom_mongo_client, logger


class MilestoneAbs(abc.ABC):

    def __init__(self, student_id, **kwargs):
        self.student_id = student_id
        self.kwargs = kwargs
        self.student_profile_obj = self.set_student_profile(self.student_id)

    @staticmethod
    def set_student_profile(student_id):
        collection = custom_mongo_client.get_collection('Students_App_studentprofile')
        student_profile_obj = collection.find_one({'student_id': student_id})
        return student_profile_obj

    @staticmethod
    def get_completed_milestones(value, milestone_name, subject_id=None):
        """
        This method is used in milestone classes to get a list of active milestones from milestone
        collection whose values is less than the value provided in the args.
        Args:
            value: the number less than which milestone list will be retrieved
            milestone_name: Name of the Milestone
            subject_id: only in case of chapter milestone the data is filtered with subject_id
        Returns: List of dictionaries
        """
        milestones_collection = custom_mongo_client.get_collection('data_points_milestones')
        query = {
            "milestone": milestone_name,
            "value": {"$lte": value},
            "is_deleted": False
        }
        if subject_id:
            query.update({"subject_id": subject_id})

        pipeline_query = [
            {
                '$match': {**query}
            }
        ]
        result = milestones_collection.aggregate(pipeline_query)
        return list(result)

    @staticmethod
    def create_student_milestone(user_id, student_id, milestone_obj):
        """
        This method creates data in student milestones only if the data doesn't exist
        Args: user_id, student_id, milestone_obj
        Returns:
            True: if new data created
            False: if data already exists
        """
        student_milestone_collection = custom_mongo_client.get_collection('data_points_studentmilestone')
        data = {
            "student_id": student_id,
            "user_id": user_id,
            "reward": milestone_obj.get('reward'),
            "milestone_type": milestone_obj.get('milestone'),
            "title": milestone_obj.get('title'),
            "milestone_id": milestone_obj.get('_id'),
        }

        # create data only if document doesn't exist
        result = student_milestone_collection.update_one(
            {
                **data  # filter condition
            },
            {
                "$setOnInsert": {"completed_at": datetime.datetime.now(), **data},  # if filter not match, then create
            },
            upsert=True
        )

        if result.upserted_id:
            is_created = True
        else:
            is_created = False

        return is_created

    def get_device_token(self):
        student_id = self.student_id
        # collection = custom_mongo_client.get_collection('Students_App_studentprofile')

        # query = [
        #     {
        #         '$match': {
        #             'student_id': student_id
        #         }
        #     }, {
        #         '$lookup': {
        #             'from': 'Students_App_devices',
        #             'localField': 'user_id_id',
        #             'foreignField': 'user_id',
        #             'as': 'result'
        #         }
        #     }, {
        #         '$unwind': {
        #             'path': '$result'
        #         }
        #     }, {
        #         '$replaceRoot': {
        #             'newRoot': '$result'
        #         }
        #     }, {
        #         '$project': {
        #             'token': 1
        #         }
        #     }
        # ]
        collection = custom_mongo_client.get_collection('Students_App_devices')
        query = [
            {
                '$match': {
                    'user_id': self.student_profile_obj.get('user_id_id')
                }
            }
        ]
        token_list = list(collection.aggregate(query))
        return token_list[0].get("token")

    def send_complete_notification(self, milestone_obj):
        try:
            device_token = self.get_device_token()
            data = {
                'task': 'milestone',
                'image': milestone_obj.get('icon'),
                'title': milestone_obj.get('title'),
                'success_description': milestone_obj.get('description'),
                'reward_message': milestone_obj.get('reward_message'),
                'reward_points': str(milestone_obj.get('reward')),
                'diamond': str(milestone_obj.get('diamond')),
                'completed_at': str(datetime.datetime.now())
            }

            notification_instance = NotificationFactory(platform='InAppNotification', **{}).notification_instance
            notification_instance.send_notification(
                heading=milestone_obj.get('title'),
                content=milestone_obj.get('description'),
                image_url=milestone_obj.get('icon'),
                device_token_list=[device_token],
                data=data,
                in_app=False
            )
            logger.log_info('Notification sent on complete')
        except Exception as err:
            logger.log_error(f'Milestone-> Error: {err}, function: send_complete_notification, '
                             f'lineno: {err.__traceback__.tb_lineno}')

    def set_student_reward(self, milestone_obj):
        try:
            points = milestone_obj.get('reward')
            diamond = milestone_obj.get('diamond')
            user_id = self.student_profile_obj.get('user_id_id')
            add_points_to_student(point_activity="Milestone", points=points, time=0,
                                  user_id=user_id, student_id=self.student_id)
            add_diamond_to_user(
                activity="milestone",
                user_id=user_id,
                student_id=self.student_id,
                diamond=diamond
            )
        except Exception as err:
            logger.log_error(f'Milestone-> Error: {err}, function: set_student_reward, '
                             f'lineno: {err.__traceback__.tb_lineno}')

    def send_ga_event(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_student_milestone_progress(self, start_date=None, end_date=None):
        raise NotImplementedError

    @abc.abstractmethod
    def process_milestone(self):
        raise NotImplementedError
