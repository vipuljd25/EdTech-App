from factory.calculation.calculation_abs import CalculationsAbs
from utils.common_methods import custom_mongo_client
from factory.calculation.mongo_query import chapter_query, lesson_component_query, earn_points_query, \
    mcq_set_query, reels_query_total, reels_query_one, daily_open_query
from challenges.models import StudentChallengeData
from challenges.utils import get_end_date


class ChapterProgress(CalculationsAbs):
    """
    class for getting chapter progress.
    base query is chapter progress of given input.
    chapter_id --> chapter progress
    subject_id --> all chapter of subject
    class_id --> all chapter of given class (special course.)
    student_id is required.
    """
    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('Students_App_chapter')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    @staticmethod
    def create_calculating_query(student_id, chapter_id=None):
        data = {}
        if chapter_id:
            data['chapter_id'] = chapter_id
        query = chapter_query(student_id=student_id, **data)
        return query

    def calculate(self) -> list:
        """
        Method is for calculate the chapter progress for the
        given input.
        :return: list of the chapters progress in percentage, time and point.
        """
        challenge = self.kwargs.get('challenge')
        chapter_id = self.kwargs.get('chapter_id')
        if challenge:
            chapter_id = challenge.get('challenge_info').get('chapter_id')
        query = self.create_calculating_query(self.student_id, chapter_id)
        self.results = list(self.collection.aggregate(query))
        return self.results

    def get_total_chapter(self):
        pass


class SubjectProgress(CalculationsAbs):

    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('Students_App_chapter')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    @staticmethod
    def create_calculating_query(student_id, subject_id=None):
        data = {}
        if subject_id:
            data['subject_id_id'] = subject_id
        query = chapter_query(student_id=student_id, **data)
        return query

    def calculate(self):
        """
        Method is used to calculate the chapter progress
        for given parameters.
        :return:
        """
        subject_progress = {
            'Percentage': 0,
            'Points': 0,
            'Minute': 0
        }
        challenge = self.kwargs.get('challenge')
        subject_id = self.kwargs.get('subject_id')

        if challenge:
            subject_id = challenge.get('challenge_info').get('subject_id')

        query = self.create_calculating_query(self.student_id, subject_id)

        all_chapters = list(self.collection.aggregate(query))
        for chapter in all_chapters:
            chapter.pop('_id')  # _id can not be added
            for value in chapter:
                subject_progress[value] += chapter[value]
        # convert percentage of subject
        subject_progress['Percentage'] = subject_progress['Percentage'] / len(all_chapters)
        self.results = [subject_progress]
        return self.results


class SpecialCourse(CalculationsAbs):
    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('Students_App_chapter')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    @staticmethod
    def create_calculating_query(student_id, class_id=None):
        data = {}
        if class_id:
            data['class_id_id'] = class_id
        query = chapter_query(student_id=student_id, **data)
        return query

    def calculate(self):
        """
        Method is used to calculate the chapter progress
        for given parameters.
        :return:
        """
        course_progress = {
            'Percentage': 0,
            'Points': 0,
            'Minute': 0
        }
        challenge = self.kwargs.get('challenge')
        class_id = self.kwargs.get('class_id')

        if challenge:
            class_id = challenge.get('challenge_info').get('class_id')

        query = self.create_calculating_query(self.student_id, class_id)

        all_chapters = list(self.collection.aggregate(query))
        for chapter in all_chapters:
            chapter.pop('_id')  # _id can not be added
            for value in chapter:
                course_progress[value] += chapter[value]

        # convert percentage of subject
        course_progress['Percentage'] = course_progress['Percentage'] / len(all_chapters)
        self.results = [course_progress]
        return self.results


class ReelBaseClass(CalculationsAbs):
    TOTAL = True
    AI_GENERATED = False

    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('data_points_reelsattempt')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    def calculate(self):
        """
        Method is used to calculate the total reels attempted by student
        for given parameters.
        :return: {'questions_attempt': 0, 'correct': 0, 'incorrect': 0, 'time': 0, 'points': 0}
        """
        query = {}
        subject_id = self.kwargs.get('subject_id')

        if self.kwargs.get('subject_wise', False):
            query.update({"subject_id": subject_id})

        challenge_subject_id = self.kwargs.get('subject_id', 0)

        if challenge := self.kwargs.get('challenge', {}):
            challenge_info = challenge.get('challenge_info')
            challenge_subject_id = challenge_info.get('subject_id')

            query = {'ai_generated': self.AI_GENERATED,
                     'created_at': {
                         '$gte': challenge.get('start_date'),
                         '$lte': challenge.get('end_date'),
                     }
                     }

        if self.TOTAL:
            query = reels_query_total(
                student_id=self.student_id,
                **query
            )
            self.results = list(self.collection.aggregate(query))
        else:
            attempts = 0
            points = 0
            if subject_id == challenge_subject_id and self.AI_GENERATED == self.kwargs.get('ai_generated'):
                attempts = self.kwargs.get('total_reels')
                points = self.kwargs.get("points")
            data = {
                "QuestionsAttempt": attempts,
                "Points": points
            }
            self.results = [data]
        return self.results


class TotalReels(ReelBaseClass):
    TOTAL = True


class TeacherGeneratedInOneSession(ReelBaseClass):
    TOTAL = False
    AI_GENERATED = False


class TeacherGeneratedTotal(ReelBaseClass):
    TOTAL = True
    AI_GENERATED = False


class AIReelsInOneSession(ReelBaseClass):
    TOTAL = False
    AI_GENERATED = True


class AIReelsTotal(ReelBaseClass):
    TOTAL = True
    AI_GENERATED = True


class MCQSet(CalculationsAbs):
    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('mcq_mcqfirstattempt')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    def calculate(self):
        """
        Method is used to calculate the total reels attempted by student
        for given parameters.
        :return: {'questions_attempt': 0, 'correct': 0, 'incorrect': 0, 'time': 0, 'points': 0}
        """
        subject_id = self.kwargs.get('subject_id')
        chapter_id = self.kwargs.get('chapter_id')

        if challenge := self.kwargs.get('challenge'):
            subject_id = challenge.get('challenge_info').get('subject_id')
            chapter_id = challenge.get('challenge_info').get('chapter_id')

        query = mcq_set_query(student_id=self.student_id, **{"subject_id": subject_id, "chapter_id": chapter_id})
        self.results = list(self.collection.aggregate(query))
        return self.results


class LessonComponent(CalculationsAbs):

    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('data_points_studentelementtime')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    def calculate(self):
        """
        Method is used to calculate the total reels attempted by student
        for given parameters.
        :return: {'questions_attempt': 0, 'correct': 0, 'incorrect': 0, 'time': 0, 'points': 0}
        """
        element_type = self.kwargs.get('component_type')
        start_date = self.kwargs.get('start_date')
        end_date = self.kwargs.get('end_date')

        challenge = self.kwargs.get('challenge')
        if challenge:
            element_type = challenge.get('challenge_info').get('component_type')
            if element_type == 'LOTTY':
                element_type = 'json'
            start_date = challenge.get('start_date')
            end_date = challenge.get('end_date')

        query = lesson_component_query(student_id=self.student_id,
                                       **{'element_type': element_type, 'start_date': start_date, 'end_date': end_date})
        self.results = list(self.collection.aggregate(query))
        return self.results


class EarnPoints(CalculationsAbs):
    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('data_points_studenttimepoints')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    def calculate(self):
        """
        :return:
        """
        start_date = self.kwargs.get('start_date'),
        end_date = self.kwargs.get('end_date')

        challenge = self.kwargs.get('challenge')
        if challenge:
            start_date = challenge.get('start_date')
            end_date = challenge.get('end_date')

        query = earn_points_query(
            student_id=self.student_id,
            **{"start_date": start_date, "end_date": end_date}
        )
        self.results = list(self.collection.aggregate(query))
        return self.results


class DailyAppOpen(CalculationsAbs):

    def set_collection(self):
        self.collection = custom_mongo_client.get_collection('data_points_studenttimepoints')

    def is_calculation_in_timeframe(self):
        pass

    def get_timeframe(self):
        pass

    def calculate(self):
        """
        :return:
        """
        start_date = self.kwargs.get('start_date')
        end_date = self.kwargs.get('end_date')

        challenge = self.kwargs.get('challenge')
        time_kwargs = {}

        if challenge:
            challenge_id = challenge.get('_id')
            student_challenge_obj = StudentChallengeData.objects.filter(
                challenge=challenge_id,
                student_id=self.student_id
            ).first()

            timeframe = challenge.get('challenge_info').get('timeframe')
            start_date = student_challenge_obj.accepted_at
            end_date = get_end_date(timeframe, start_date)

        if start_date and end_date:
            time_kwargs = {
                'created_at': {'$gte': start_date, '$lte': end_date}
            }

        query = daily_open_query(
            student_id=self.student_id,
            **time_kwargs
        )
        self.results = list(self.collection.aggregate(query))
        return self.results
