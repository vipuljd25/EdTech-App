import datetime
from factory.challenge.challenge_abs import ChallengeAbs
from challenges.models import ChallengeData, StudentChallengeData
from utils.common_methods import perform_comparison, logger
from events.ga_events import send_ga_event
from data_points.utils import add_points_to_student, add_diamond_to_user


class BaseChallenge(ChallengeAbs):
    """
    Base challenge class for challenges.
    """
    @staticmethod
    def set_challenge_progress(unit_value, current_value, student_challenge_obj):
        percentage = current_value*100/unit_value
        percentage = percentage if percentage < 100 else 100
        student_challenge_obj.progress = percentage
        student_challenge_obj.save()

    def is_challenge_completed(self, calculating_instance, challenge, student_challenge_obj):
        result = None
        current_value = None
        comparison_operator = challenge['challenge_info'].get('comparison_operator')

        unit_key = challenge['challenge_info'].get('unit_key').replace(' ', '')
        unit_value = challenge['challenge_info'].get('unit_value')

        if unit_key == 'Minute':
            unit_value = unit_value * 60000
        calculation_obj = calculating_instance.calculate()
        if isinstance(calculation_obj, list) and calculation_obj:
            current_value = calculation_obj[0].get(unit_key)

        if current_value:
            result = perform_comparison(unit_value, current_value, comparison_operator)
            if challenge['challenge_info'].get('sub_challenge') not in self.unset_progress_array:
                self.set_challenge_progress(unit_value, current_value, student_challenge_obj)

        return result

    def mark_challenge_completed(self, student_challenge_obj):

        if student_challenge_obj:
            student_challenge_obj.status = 'COMPLETED'
            student_challenge_obj.completed_at = datetime.datetime.now()
            student_challenge_obj.save()
            logger.log_info(f'marked complete for student_id: {self.student_id} and '
                            f'challenge_id: {student_challenge_obj.challenge_id}')
        else:
            logger.log_info(f'something went wrong in mark_challenge_complete')

    def assign_points(self, reward_points, user_id, diamond):
        add_points_to_student(
            points=reward_points,
            time=0,
            user_id=user_id,
            student_id=self.student_id,
            point_activity="challenge"
        )
        add_diamond_to_user(
            activity="challenge",
            user_id=user_id,
            student_id=self.student_id,
            diamond=diamond
        )

    def sent_completed_notification(self, challenge, student_challenge_obj):

        challenge_success = challenge.get('after_success')
        notification_instance = self.get_notification_instance(platform="InAppNotification", **{})
        device_token_list = self.get_device_token(student_challenge_obj)  # to find the device token of students
        data = {
            'task': 'challenge',
            'image': challenge_success.get('success_image'),
            'title': challenge_success.get('success_sub_title'),
            'success_description': challenge_success.get('success_description'),
            'reward_message': challenge.get('reward_message'),
            'reward_points': str(challenge.get('reward_points'))
        }
        notification_instance.send_notification(
            heading=challenge_success.get('success_sub_title'),
            content=challenge_success.get('success_description'),
            image_url=challenge_success.get('success_image'),
            device_token_list=device_token_list,
            data=data,
            in_app=False
        )
        logger.log_info('Notification sent on complete')

    def check_challenge_completed(self):
        logger.log_info(f'Check challenge for {self.student_id}')
        for challenge in self.challenges:
            try:
                self.kwargs.update({'challenge': challenge})
                calculation_instance = self.get_calculation_instance(
                    student_id=self.student_id, challenge_obj=challenge, **self.kwargs
                )
                challenge_id = challenge.get("_id")
                student_challenge_obj = StudentChallengeData.objects.filter(
                    challenge_id=challenge_id, student_id=self.student_id).first()
                if self.is_challenge_completed(calculation_instance, challenge, student_challenge_obj):
                    self.mark_challenge_completed(student_challenge_obj)
                    reward_points = challenge.get('reward_points') or 0
                    diamond = challenge.get('diamond') or 0
                    self.assign_points(reward_points, student_challenge_obj.user_id, diamond)
                    # send_ga_event(
                    #     event_name="Challenge_Complete",
                    #     **{"student_id": self.student_id, "challenge_complete": True}
                    # )  # TODO rahul gupta
                    self.sent_completed_notification(challenge, student_challenge_obj)
            except Exception as err:
                logger.log_error(f'Getting Error for challenge {challenge.get("_id")} for student {self.student_id}')
