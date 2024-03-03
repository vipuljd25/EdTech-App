# used in consumer to find the challenge from model
EVENTS_MODEL = {
    'lessonProgress': 'lesson_progress',
    'McqFirstAttempt': 'mcq_set',
    'StudentTimePoints': 'earn_points',
    'StudentElementTime': 'lesson_component',
}
CHALLENGES = {
    'lesson_progress': 'Lesson',
    'mcq_set': 'MCQ Set',
    'earn_points': 'Earn Points',
    'lesson_component': 'Lesson Component',
}
SUB_CHALLENGES = {
    'Lesson': ["Lesson Progress", "Subject Progress", "Special Course"],
    'MCQs': [
        "Teacher Generated Total MCQ",
        "AI MCQ In One Session", "AI MCQ Total"
    ],
    'MCQ Set': ["MCQ Set"],
    'Earn Points': ["Earn Points"],
    'Lesson Component': ["Lesson Component"],
}
MILESTONES = {
    'PartsProgress': 'TotalLesson',
    'MCQAttempt': "TotalMCQsAttempts",
    'custom_daily_open': 'DailyOpen'
}