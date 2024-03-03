from bson import ObjectId

from data_points.models import Subjects, Chapter
from factory.calculation.factory import CalculationFactory
from utils.common_methods import custom_mongo_client, logger, perform_comparison
from .nudges_abs import NudgesAbs
from factory.calculation.factory import CalculationFactory


class ChapterProgress(NudgesAbs):

    def is_satisfy_condition(self, nudges):
        try:
            nudges_info = nudges.get('nudges_info')
            requested_chapter_id = self.kwargs.get('chapter_id', None)
            chapter_id = nudges_info.get('chapter_id', None)

            trigger_key = nudges.get('trigger_key').lower()
            initial_trigger_value = nudges.get('initial_trigger_value')
            final_trigger_value = nudges.get('final_trigger_value')
            check = True

            if chapter_id and not chapter_id == requested_chapter_id:
                check = False

            if check and initial_trigger_value <= self.kwargs.get(trigger_key) < final_trigger_value:
                return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):
        nudges_type_to_fetch = ["Chapter Progress"]
        logger.log_info(f"Nudges-> processing {nudges_type_to_fetch} Nudges for student_id: {self.student_id}")
        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                # check if data already exists
                # TODO need to check any chapter is flaged or not.
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge_data, student_nudge_data):
        try:
            trigger_key = nudge_data.get('trigger_key')
            final_trigger_value = nudge_data.get('final_trigger_value')
            condition = nudge_data.get('check_parameter')
            current_value = 0

            calculation_obj = CalculationFactory(self.student_id, 'ChapterProgress',
                                                 **{'chapter_id': self.kwargs.get('chapter_id')}
                                                 ).create_instance().calculate()

            if isinstance(calculation_obj, list) and calculation_obj:
                current_value = calculation_obj[0].get(trigger_key)

            result = perform_comparison(final_trigger_value, current_value, condition)
            return result
        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        student_name, chapter_name, subject_name, unit_completed, percentage
        """
        student_name = self.student_profile_obj.get('first_name')
        chapter_obj = Chapter.objects.filter(chapter_id=nudge_data.get('nudges_info').get('chapter_id')).first()

        chapter_name = chapter_obj.chapter_name
        subject_name = Subjects.objects.filter(subject_id=chapter_obj.subject_id_id).values('subject_name').first().get('subject_name')
        trigger_key = nudge_data.get("trigger_key")

        current_value = 0
        calculation_obj = CalculationFactory(self.student_id, 'ChapterProgress',
                                             **{'chapter_id': self.kwargs.get('chapter_id')}
                                             ).create_instance().calculate()

        if isinstance(calculation_obj, list) and calculation_obj:
            current_value = calculation_obj[0].get(trigger_key)

        response = {
            "student_name": student_name,
            "chapter_name": chapter_name,
            "subject_name": subject_name,
            "unit_completed": trigger_key,
            "current_value": current_value
        }

        return response


class SpecialCourseProgress(ChapterProgress):

    def is_satisfy_condition(self, nudges):
        try:
            nudges_info = nudges.get('nudges_info')
            requested_chapter_id = self.kwargs.get('chapter_id', None)
            chapter_id = nudges_info.get('chapter_id', None)

            trigger_key = nudges.get('trigger_key')
            initial_trigger_value = nudges.get('initial_trigger_value')
            final_trigger_value = nudges.get('final_trigger_value')

            calculation_instance = CalculationFactory(self.student_id, calculation="SpecialCourse",
                                                      **self.kwargs).create_instance()
            result = calculation_instance.calculate()

            check = True
            if chapter_id and not chapter_id == requested_chapter_id:
                check = False

            if check and initial_trigger_value <= result[0].get(trigger_key) < final_trigger_value:
                return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):
        nudges_type_to_fetch = ["Special Course Progress"]
        logger.log_info(f"Nudges-> processing {nudges_type_to_fetch} Nudges for student_id: {self.student_id}")

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge_data, student_nudge_data):
        try:
            trigger_key = nudge_data.get('trigger_key')
            final_trigger_value = nudge_data.get('final_trigger_value')
            condition = nudge_data.get('check_parameter')
            current_value = 0

            calculation_obj = CalculationFactory(self.student_id, 'SpecialCourse',
                                                 **{'chapter_id': self.kwargs.get('class_id')}
                                                 ).create_instance().calculate()

            if isinstance(calculation_obj, list) and calculation_obj:
                current_value = calculation_obj[0].get(trigger_key)

            result = perform_comparison(final_trigger_value, current_value, condition)
            return result
        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        student_name, chapter_name, subject_name, unit_completed, percentage
        """
        student_name = self.student_profile_obj.get('first_name')
        response = {
            "student_name": student_name
        }
        return response


class TotalReels(NudgesAbs):
    def is_satisfy_condition(self, nudges):
        try:

            trigger_key = nudges.get('trigger_key').replace(" ", "")
            initial_trigger_value = nudges.get('initial_trigger_value')
            final_trigger_value = nudges.get('final_trigger_value')

            calculation = "TotalReels"

            calculation_instance = CalculationFactory(self.student_id, calculation=calculation,
                                                      **self.kwargs).create_instance()
            result = calculation_instance.calculate()

            if initial_trigger_value <= result[0].get(trigger_key) < final_trigger_value:
                return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):
        nudges_type_to_fetch = ["Chapter Progress"]
        logger.log_info(f"Nudges-> processing {nudges_type_to_fetch} Nudges for student_id: {self.student_id}")

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge_data, student_nudge_data):
        try:
            trigger_key = nudge_data.get('trigger_key').replace(' ', '')
            final_trigger_value = nudge_data.get('final_trigger_value')
            condition = nudge_data.get('check_parameter')
            current_value = 0

            calculation_obj = CalculationFactory(self.student_id, 'TotalReels',
                                                 **{}
                                                 ).create_instance().calculate()

            if isinstance(calculation_obj, list) and calculation_obj:
                current_value = calculation_obj[0].get(trigger_key)

            result = perform_comparison(final_trigger_value, current_value, condition)
            return result
        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        Student Name,
        reels quantity = total number of reels solved
        """
        student_name = self.student_profile_obj.get('first_name')

        calculation_obj = CalculationFactory(self.student_id, 'TotalReels', **{}).create_instance().calculate()
        trigger_key = nudge_data.get('trigger_key').replace(' ', '')

        reels_quantity = calculation_obj[0].get(trigger_key)

        response = {
            "student_name": student_name,
            "reels_quantity": reels_quantity
        }

        return response


class AIGeneratedReelsOnTopic(NudgesAbs):

    def is_satisfy_condition(self, nudges):
        try:
            instance_topic_id = self.kwargs.get('subject_id')
            nudge_topic_id = nudges.get("nudges_info").get("subject_id")

            trigger_key = nudges.get('trigger_key').replace(" ", "")
            initial_trigger_value = nudges.get('initial_trigger_value')
            final_trigger_value = nudges.get('final_trigger_value')

            calculation = "AIReelsTotal"
            self.kwargs.update({"subject_wise": True})
            if instance_topic_id == nudge_topic_id:
                calculation_instance = CalculationFactory(self.student_id, calculation=calculation,
                                                          **self.kwargs).create_instance()
                result = calculation_instance.calculate()

                if initial_trigger_value <= result[0].get(trigger_key) < final_trigger_value:
                    return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):

        nudges_type_to_fetch = ["AI Generated Reels on Topic"]

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                nudges_type = nudges.get('nudges_type')
                logger.log_info(f"Nudges-> processing {nudges_type} Nudges for student_id: {self.student_id}")
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged"
                                    f"{nudges_type} Nudges for student_id: {self.student_id}")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge_data, student_nudge_data):
        try:
            trigger_key = nudge_data.get('trigger_key').replace(' ', '')
            final_trigger_value = nudge_data.get('final_trigger_value')
            condition = nudge_data.get('check_parameter')
            current_value = 0

            calculation_obj = CalculationFactory(self.student_id, 'AIReelsInOneSession',
                                                 **{'ai_generated': True, 'subject_id': self.kwargs.get('subject_id')}
                                                 ).create_instance().calculate()

            if isinstance(calculation_obj, list) and calculation_obj:
                current_value = calculation_obj[0].get(trigger_key)

            result = perform_comparison(final_trigger_value, current_value, condition)
            return result
        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        Student Name, Reels Topic, Qty. of Reels Solved,  Name of Topic Expected, Qty. of reels expected to be solved.
        """
        student_name = self.student_profile_obj.get('first_name')
        reels_topic = Subjects.objects.filter(
            subject_id=self.kwargs.get('subject_id')).values("subject_name").first().get("subject_name")
        quantities_of_reels_solved = self.kwargs.get('total_reels')
        response = {
            "student_name": student_name,
            "reels_topic": reels_topic,
            "quantities_of_reels_solved": quantities_of_reels_solved,
            "name_of_topic_expected": reels_topic,
            "quantity_of_reels_expected_to_be_solved": reels_topic,
            "wait_duration": "wait"  # TODO wait duration
        }
        return response


class KnowledgeReels(NudgesAbs):
    def is_satisfy_condition(self, nudges):
        return True

    def process_nudges(self):

        if self.kwargs.get('ai_generated'):
            nudges_type_to_fetch = ["KnowledgeReelsAIMade"]

        else:
            nudges_type_to_fetch = ["KnowledgeReelsTeacherMade"]

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                nudges_type = nudges.get('nudges_type')
                logger.log_info(f"Nudges-> processing {nudges_type} Nudges for student_id: {self.student_id}")
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge, student_nudge):
        # User has not attempted any more question / User has attempted question

        student_flagged_datetime = student_nudge.get("created_at")
        reels_attempt_collection = custom_mongo_client.get_collection('data_points_reelsattempt')
        reels_attempt_obj = reels_attempt_collection.find_one(
            {
                "student_id": self.student_id,
                "created_at": {"$gt": student_flagged_datetime}
            }
        )

        check_condition = student_nudge.get('check_condition')

        if reels_attempt_obj and check_condition == 'User has attempted question':
            # send true when User has attempted question
            return True

        if not reels_attempt_obj and not check_condition == 'User has not attempted any more question':
            # send true when User has not attempted any more question
            return True

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        Student Name, Last reel Subject Solved, Date when solved , Time when solved
        """
        student_name = self.student_profile_obj.get('first_name')
        last_reel_subject_solved = Subjects.objects.filter(
            subject_id=self.kwargs.get('subject_id')).values("subject_name").first().get("subject_name")
        date_when_solved = student_nudge_data.get('created_at').date()
        time_when_solved = student_nudge_data.get('created_at').time()

        response = {
            "student_name": student_name,
            "last_reel_subject_solved": last_reel_subject_solved,
            "date_when_solved": str(date_when_solved),
            "time_when_solved": str(time_when_solved)
        }
        return response


class Challenges(NudgesAbs):
    def is_satisfy_condition(self, nudges):
        try:
            instance_challenge_id = ObjectId(self.kwargs.get('challenge_id'))
            nudge_challenge_id = nudges.get("nudges_info").get("challenge_id")

            if nudge_challenge_id:
                if nudge_challenge_id == instance_challenge_id:
                    return True
            else:
                return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):

        nudges_type_to_fetch = ["Challenges"]

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                nudges_type = nudges.get('nudges_type')
                logger.log_info(f"Nudges-> processing {nudges_type} Nudges for student_id: {self.student_id}")
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge, student_nudge):
        # challenge Completed or Not Completed
        student_nudge_id = student_nudge.get('_id')
        challenge_id = nudge.get('nudge_info').get('challenge_id')
        student_challenge_collection = custom_mongo_client.get_collection('challenges_studentchallengedata')
        student_challenge_obj = student_challenge_collection.find_one({"challenge_id": challenge_id})

        if student_challenge_obj.get('challenge_status') == 'EXPIRED':
            return False  # TODO when challenge is expired turn off nudge

        else:

            check_condition = student_nudge.get('check_condition')
            status = student_challenge_obj.get('status')

            if check_condition == 'Completed' and status == 'COMPLETED':
                return True

            if check_condition == 'Not-Completed' and not status == 'COMPLETED':
                return True

        return False

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        returns: Student Name, ChallengeName
        """
        student_name = self.student_profile_obj.get('first_name')
        challenge_name = self.kwargs.get('challenge_title')
        # TODO or is it? ->  self.kwargs.get('challenge_display').get('display_sub_title')

        response = {
            "student_name": student_name,
            "challenge_name": challenge_name
        }
        return response


class Milestone(NudgesAbs):

    def is_satisfy_condition(self, nudges):
        try:
            instance_milestone_id = self.kwargs.get('milestone_id')
            nudge_milestone_id = nudges.get("nudges_info").get("milestone_id")

            if nudge_milestone_id:
                if nudge_milestone_id == instance_milestone_id:
                    return True
            else:
                return True

            return False

        except Exception as err:
            logger.log_error(f"Nudges-> error in function is_satisfy_condition, /"
                             f"Error: {err}, line_no: {err.__traceback__.tb_lineno}")

    def process_nudges(self):

        nudges_type_to_fetch = ["Milestone"]

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                nudges_type = nudges.get('nudges_type')
                logger.log_info(f"Nudges-> processing {nudges_type} Nudges for student_id: {self.student_id}")
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge, student_nudge):
        # TODO when milestone is deactivated turn off nudge
        # milestone Completed or Not Completed
        check_condition = student_nudge.get('check_condition')
        check_parameter = student_nudge.get('check_parameter')

        if check_parameter == "Other Milestone":

            student_flagged_datetime = student_nudge.get("created_at")
            student_challenge_collection = custom_mongo_client.get_collection('data_points_studentmilestone')
            milestone_obj = student_challenge_collection.find_one(
                {
                    "student_id": self.student_id,
                    "created_at": {"$gt": student_flagged_datetime}
                }
            )

            if milestone_obj and check_condition == 'Completed':
                # other milestone Completed
                return True

            if not milestone_obj and not check_condition == 'Completed':
                # other milestone Not-Completed
                return True

        if check_parameter == "None":
            return True

        return False

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        Student Name, Completed Milestone Name
        """
        student_name = self.student_profile_obj.get('first_name')
        milestone_name = self.kwargs.get('milestone_name')

        response = {
            "student_name": student_name,
            "milestone_name": milestone_name
        }
        return response


class McqQuestionSetInChapter(NudgesAbs):

    def is_satisfy_condition(self, nudges):
        return True

    def process_nudges(self):

        nudges_type_to_fetch = ["Mcq Question Set In Chapter"]

        try:
            all_nudges = self.fetch_all_nudges(nudges_type_to_fetch)
            for nudges in all_nudges:
                nudges_type = nudges.get('nudges_type')
                logger.log_info(f"Nudges-> processing {nudges_type} Nudges for student_id: {self.student_id}")
                # check if data already exists
                is_flagged = self.is_flagged(nudges)

                if not is_flagged:
                    # If data doesn't exist check for the given condition
                    if self.is_satisfy_condition(nudges):
                        student_nudge = self.set_student_nudges(nudges)
                        self.scheduled_task(nudges, student_nudge)
                else:
                    logger.log_info(f"Nudges-> student already flagged")

        except Exception as err:
            logger.log_error(f"Nudges-> Error in process_nudges for student_id: {self.student_id} /"
                             f"--> Error: {err}, lineno: {err.__traceback__.tb_lineno}")

    def decision_maker(self, nudge, student_nudge):
        # No other MCQ Question set has been attempted
        student_nudge_id = student_nudge.get('_id')
        student_flagged_datetime = student_nudge.get("created_at")

        collection = custom_mongo_client.get_collection('mcq_mcqfirstattempt')
        new_mcq_count = collection.find_one({"created_at": {"$gt": student_flagged_datetime}})

        if new_mcq_count:
            return False
        else:
            return True

    def get_template_variables(self, nudge_data, student_nudge_data):
        """
        returns: Student Name, MCQ question set Name
        """
        student_name = self.student_profile_obj.get('first_name')
        mcq_question_set_name = "abc"  # TODO find mcq set name

        response = {
            "student_name": student_name,
            "mcq_question_set_name": mcq_question_set_name
        }
        return response
