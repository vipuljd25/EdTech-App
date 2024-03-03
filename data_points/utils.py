from data_points.models import StudentTimePoints, StudentProfile
from data_points.models import Diamond


def add_points_to_student(point_activity, points, time, user_id, student_id):
    """
    function used to add points to StudentTimePoints collection based for different activity
    """
    student_obj = StudentProfile.objects.filter(user_id=user_id, student_id=student_id).first()
    StudentTimePoints.objects.create(
        point_activity=point_activity, points=points, student_id=student_obj.student_id,
        time=time, school_id=student_obj.school_id_id, class_id=student_obj.class_id_id,
        medium_id=student_obj.medium_id_id, user_id=user_id
    )


def add_diamond_to_user(activity, diamond, user_id, student_id):
    """
    function used to add diamond to Diamond collection based for different activity
    """
    student_obj = StudentProfile.objects.filter(user_id=user_id, student_id=student_id).first()
    Diamond.objects.create(
        activity=activity, diamond=diamond, school_id=student_obj.school_id_id,
        class_id=student_obj.class_id_id, medium_id=student_obj.medium_id_id,
        user_id=user_id, student_id=student_id
    )
