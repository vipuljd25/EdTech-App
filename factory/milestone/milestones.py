import datetime
import json

from factory.milestone.milestone_abs import MilestoneAbs
from student_activity.redis_sync import student_total_points_sync
from utils.common_methods import logger, custom_mongo_client
from factory.calculation.calculations import ChapterProgress, ReelBaseClass, EarnPoints, DailyAppOpen
from factory.calculation.mongo_query import highest_value_milestone_query


class TotalChapter(MilestoneAbs):

    def get_student_milestone_progress(self, start_date=None, end_date=None):
        """
        This method is used to find the no. of chapters of a particular subject that is completed by the student
        here, subject_id is from the instance so this method finds how many chapters has been completed for that subject
        Returns: Number
        """
        chapter_progress_collection = custom_mongo_client.get_collection('data_points_chapterprogress')
        query = [
            {
                '$match': {
                    'student_id': self.student_id,
                    'subject_id': self.kwargs.get('subject_id'),
                    'percentage': 100
                }
            }, {
                '$count': 'count'
            }
        ]
        chapters_list_cursor = chapter_progress_collection.aggregate(query)
        chapters_list = list(chapters_list_cursor)
        completed_chapter_count = chapters_list[0].get('count')
        return completed_chapter_count

    def process_milestone(self):
        """
        This Method is used to process milestone for a student and
            -> check completed chapters for the subject_id of instance
            -> get only completed chapter milestones that exists for that subject
            -> mark milestone if completed
            -> send notification when complete
            -> add points to student_time_points with activity milestone
            -> TODO send GA
        Returns: None
        """
        milestone_name = "Total Chapter"
        subject_id = self.kwargs.get("subject_id")
        logger.log_info(f'Milestone: Processing {milestone_name}, subject_id: {subject_id},'
                        f' Milestone for student_id: {self.student_id}')
        try:
            completed_chapter_count = self.get_student_milestone_progress()
            if completed_chapter_count:

                completed_milestones_list = self.get_completed_milestones(completed_chapter_count,
                                                                          milestone_name, subject_id)
                for milestone_obj in completed_milestones_list:
                    is_created = self.create_student_milestone(self.student_profile_obj.get('user_id_id'),
                                                               self.student_id, milestone_obj)
                    if is_created:
                        logger.log_info(f'Milestone: {milestone_name} Milestone ({milestone_obj.get("value")}) '
                                        f'Marked Complete for student_id: {self.student_id}')

                        self.send_complete_notification(milestone_obj)
                        self.set_student_reward(milestone_obj)
                        # TODO- send_ga_event():
        except Exception as err:
            logger.log_error(
                f'Milestone-> error generated in TotalChapter '
                f'error = {err}, line_no: {err.__traceback__.tb_lineno}'
            )


class TotalReelsAttempts(MilestoneAbs):
    def get_student_milestone_progress(self, start_date=None, end_date=None):
        """
        This method is used to find the no. of reels attempted by a student
        Returns: Number
        """
        reels_attempt_calculation_instance = ReelBaseClass(self.student_id, **{})
        total_attempt_list = reels_attempt_calculation_instance.calculate()
        total_attempt = 0
        if total_attempt_list:
            total_attempt = total_attempt_list[0].get('QuestionsAttempt')

        return total_attempt

    def process_milestone(self):
        """
        This Method is used to process milestone for a student and
            -> get total reels attempted by a student
            -> get list of all completed milestones
            -> mark milestone if new milestone completed
            -> send notification when complete
            -> add points to student_time_points with activity milestone
            -> TODO send GA
        Returns: None
        """
        milestone_name = "Total Reels Attempts"
        logger.log_info(f'Milestone: Processing {milestone_name} Milestone for student_id: {self.student_id}')
        try:
            total_reels_attempt = self.get_student_milestone_progress()
            completed_milestones_list = self.get_completed_milestones(total_reels_attempt, milestone_name)

            for milestone_obj in completed_milestones_list:
                is_created = self.create_student_milestone(self.student_profile_obj.get('user_id_id'),
                                                           self.student_id, milestone_obj)
                if is_created:
                    logger.log_info(
                        f'Milestone: {milestone_name} Milestone ({milestone_obj.get("value")}) Marked Complete for '
                        f'student_id: {self.student_id}')

                    self.send_complete_notification(milestone_obj)
                    self.set_student_reward(milestone_obj)
                    # TODO- send_ga_event():
        except Exception as err:
            logger.log_error(
                f'Milestone-> error generated in TotalReelsAttempts/'
                f'error = {err}/'
                f'line_no: {err.__traceback__.tb_lineno}'
            )


# class TotalPointsEarn(MilestoneAbs):
#
#     def get_student_milestone_progress(self, start_date=None, end_date=None):
#         """
#         This method is used to find total points collected by a student, takes from redis
#         Returns: Number
#         """
#
#         total_points = 0
#
#         # get total points of student from redis
#         redis_key = f'total_points_{self.student_id}'
#         data = student_total_points_sync.get_data(key=redis_key)
#         if data:
#             data = json.loads(data)
#             total_points = data.get("total_points")
#
#         return total_points
#
#     def process_milestone(self):
#         """
#         This Method is used to process milestone for a student and
#             -> get total reels attempted by a student
#             -> get completed milestones
#             -> mark milestone if completed
#             -> TODO send notification when complete
#             -> TODO add points to student_time_points table with activity milestone
#             -> TODO send GA
#         Returns: None
#         """
#         milestone_name = "Total Points Earn"
#         logger.log_info(f'Milestone: Processing {milestone_name} Milestone for student_id: {self.student_id}')
#         try:
#             total_points = self.get_student_milestone_progress()
#             completed_milestones_list = self.get_completed_milestones(total_points, milestone_name)
#
#             for milestone_obj in completed_milestones_list:
#                 is_created = self.create_student_milestone(self.student_profile_obj.get('user_id_id'),
#                                                            self.student_id, milestone_obj)
#                 if is_created:
#                     # TODO- send_complete_notification():
#                     # TODO- set_student_reward():
#                     # TODO- send_ga_event():
#                     logger.log_info(
#                         f'Milestone: {milestone_name} Milestone ({milestone_obj.get("value")}) Marked Complete for '
#                         f'student_id: {self.student_id}')
#         except Exception as err:
#             logger.log_error(
#                 f'Milestone-> error generated in TotalPointsEarn/'
#                 f'error = {err}/'
#                 f'line_no: {err.__traceback__.tb_lineno}'
#             )
#
#
# class DailyOpen(MilestoneAbs):
#
#     @staticmethod
#     def get_timeframe(value):
#         end_date = datetime.datetime.utcnow()
#         start_date = end_date - datetime.timedelta(days=value)
#
#         return start_date, end_date
#
#     @staticmethod
#     def get_highest_value_milestone(student_id, milestone_name):
#         """
#         This method will find the daily open milestone with the highest value that the student has already completed
#         """
#         milestones_collection = custom_mongo_client.get_collection('data_points_studentmilestone')
#         highest_value_query = highest_value_milestone_query(student_id, **{"milestone_name": milestone_name})
#         result = list(milestones_collection.aggregate(highest_value_query))
#         if result:
#             highest_value_milestone = result[0].get('highestValueMilestone')
#         else:
#             highest_value_milestone = 0
#
#         return highest_value_milestone
#
#     def get_student_milestone_progress(self, start_date=None, end_date=None):
#         """
#         This method is used to find total daily app open by a student
#         Returns: Number
#         """
#         total_days_open = 0
#
#         total_points_calculation_instance = DailyAppOpen(
#             self.student_id, **{"start_date": start_date, "end_date": end_date})
#         total_points_list = total_points_calculation_instance.calculate()
#
#         if total_points_list:
#             total_days_open = total_points_list[0].get('day')
#
#         return total_days_open
#
#     def process_milestone(self):
#         """
#         This Method is used to process milestone for a student and
#             -> get latest completed daily open milestone and get its value
#             -> get list of milestones that are higher then the value and not completed
#             -> sort the list(ascending) and pick 1st element i.e the next milestone to be completed
#             -> get time timeframe depending on the value of next milestone
#             -> check the number of days app opened in the given timeframe
#             -> mark milestone complete when total_days >= next milestone value
#             -> TODO send notification when complete
#             -> TODO add points to student_time_points with activity milestone
#             -> TODO send GA
#         Returns: None
#         """
#         milestone_name = "Daily Open"
#         logger.log_info(f'Milestone: Processing {milestone_name} Milestone for student_id: {self.student_id}')
#         try:
#             # get highest value milestone completed by student
#             highest_value_milestone = self.get_highest_value_milestone(self.student_id, milestone_name)
#
#             # get sorted milestone list higher than highest_value_milestone
#             milestones_collection = custom_mongo_client.get_collection('data_points_milestones')
#             remaining_result = milestones_collection.find(
#                 {
#                     "milestone": milestone_name,
#                     "value": {"$gt": highest_value_milestone},
#                     "is_deleted": False
#                 }
#             )
#             remaining_result.sort("value", 1).limit(1)
#             remaining_milestones_list = list(remaining_result)
#
#             milestone_obj = remaining_milestones_list[0]
#
#             value = milestone_obj.get('value')
#             start_date, end_date = self.get_timeframe(value)
#
#             # get total days app open in the given timeframe
#             total_days_open = self.get_student_milestone_progress(start_date, end_date)
#             if total_days_open >= value:
#                 is_created = self.create_student_milestone(self.student_profile_obj.get('user_id_id'),
#                                                            self.student_id, milestone_obj)
#                 if is_created:
#                     self.send_complete_notification()
#                     # TODO- set_student_reward():
#                     # TODO- send_ga_event():
#                     logger.log_info(
#                         f'Milestone: {milestone_name} Milestone ({milestone_obj.get("value")}) Marked Complete for '
#                         f'student_id: {self.student_id}')
#         except Exception as err:
#             logger.log_error(
#                 f'Milestone-> error generated in TotalPointsEarn, '
#                 f'error = {err}, '
#                 f'line_no: {err.__traceback__.tb_lineno}'
#             )

