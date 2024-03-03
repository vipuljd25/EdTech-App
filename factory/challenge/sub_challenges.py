# from factory.challenge.challenge_abs import ChallengeAbs
#
#
# class PartProgressChallenge(ChallengeAbs):
#     def get_calculation_instance(self, calculation_type):
#         """
#         Pass student id and calculation type and other kwargs.
#         kwargs hold variables like chapter_id, subject_id etc.
#         :param calculation_type:
#         :return:
#         """
#         return self
#
#     @staticmethod
#     def is_challenge_completed(calculating_instance, challenge_info):
#         comparison_operator = challenge_info.get('comparison_operator')
#         unit_key = challenge_info.get('unit_key')
#         unit_value = challenge_info.get('unit_value')
#         current_value = calculating_instance.get_value(unit_key)
#         result = perform_comparison(unit_value, current_value, comparison_operator)
#         return result
#
#     def check_challenge_completed(self):
#         for challenge in self.challenges:
#             challenge_info = challenge.get('challenge_info')
#             calculation_type = challenge_info.get('sub_challenge')
#
#             calculation_instance = self.get_calculating_instances(calculation_type)
#
#             if is_challenge_completed(calculation_instance, challenge_info):
#                 self.update_student_challenges()
#                 self.sent_completed_notification()
