from datetime import datetime

from django.db import models
from djongo import models as djongo_models
import time
import uuid
import json


class BaseModel(models.Model):
    """
    Base Model with created and updated time fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Users(BaseModel):
    user_types = (
        ('SUPERADMIN', 'SUPERADMIN'),
        ('ADMIN', 'ADMIN'),
        ('CONTENT-WRITER', 'CONTENT-WRITER'),
        ('STUDENT', 'STUDENT'),
    )
    status_types = (
        ('ACTIVE', 'ACTIVE'),
        ('INACTIVE', 'INACTIVE'),
    )
    user_id = models.AutoField(primary_key=True)
    mobile = models.CharField(max_length=11)
    email = models.CharField(max_length=100, blank=True, null=True)
    token = models.CharField(max_length=5000, blank=True, null=True)
    notification_token = models.CharField(max_length=5000, blank=True, null=True)
    user_type = models.CharField(choices=user_types, default='STUDENT', max_length=100)
    status = models.CharField(choices=user_types, default='ACTIVE', max_length=100)
    last_login = models.DateTimeField(default=datetime.now)

    class Meta:
        managed = False
        db_table = "Students_App_users"
    
    @property
    def is_anonymous(self):
        return False


class AdminProfile(BaseModel):
    user_types = (
        ('SUPERADMIN', 'SUPERADMIN'),
        ('ADMIN', 'ADMIN'),
        ('CONTENT-WRITER', 'CONTENT-WRITER')
    )
    gen_types = (
        ('MALE', 'MALE'),
        ('FEMALE', 'FEMALE')
    )
    admin_id = models.AutoField(primary_key=True)
    admin_code = models.CharField(max_length=250, blank=True, null=True)
    full_name = models.CharField(max_length=1000, blank=True, null=True)
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    email = models.CharField(max_length=250)
    mobile = models.CharField(max_length=10)
    user_type = models.CharField(choices=user_types, default='ADMIN', max_length=50)
    gender = models.CharField(choices=gen_types, max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=100, blank=True, null=True)
    user_id_id = models.IntegerField()
    assigned_principal = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "Students_App_adminprofile"


class StudentStates(models.Model):
    student_state_id = models.AutoField(primary_key=True)
    state_name = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.state_name)

    class Meta:
        managed = False
        db_table = "Students_App_studentstates"


class StudentDistrict(models.Model):
    student_district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=1000)
    student_state_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.district_name)

    class Meta:
        managed = False
        db_table = "Students_App_studentdistrict"


class StudentBlock(models.Model):
    student_block_id = models.AutoField(primary_key=True)
    block_name = models.CharField(max_length=1000)
    student_district_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.block_name)

    class Meta:
        managed = False
        db_table = "Students_App_studentblock"


class Schools(models.Model):
    school_id = models.AutoField(primary_key=True)
    school_name = models.CharField(max_length=5000)
    u_dise = models.CharField(max_length=1000)
    student_block_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.school_name)

    class Meta:
        managed = False
        db_table = "Students_App_schools"


class Subjects(BaseModel):
    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=200)
    subject_code = models.CharField(max_length=200, blank=True, null=True)
    class_id_id = models.IntegerField()
    medium_id_id = models.IntegerField()
    is_common_reels = models.BooleanField(default=False)
    is_subject_reels = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "Students_App_subjects"


class District(BaseModel):
    """
    Model represent the Syllabus for students alias as District.
    """
    district_id = models.AutoField(primary_key=True)
    district_name = models.CharField(max_length=100)
    district_code = models.CharField(max_length=100, blank=True, null=True)
    board_id_id = models.IntegerField()
    is_publish_to_student = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "Students_App_district"


class Medium(BaseModel):
    medium_id = models.AutoField(primary_key=True)
    medium_name = models.CharField(max_length=100)
    state_id_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "Students_App_medium"


class Classes(BaseModel):
    class_id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=100)
    class_code = models.CharField(max_length=100, blank=True, null=True)
    district_id_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "Students_App_classes"


class Boards(BaseModel):
    board_id = models.AutoField(primary_key=True)
    board_name = models.CharField(max_length=100)
    board_code = models.CharField(max_length=100, blank=True, null=True)
    state_id_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "Students_App_boards"


class Chapter(BaseModel):
    status_options = (
        ('PUBLISHED', 'PUBLISHED'),
        ('IN-REVIEW', 'IN-REVIEW'),
        ('IN-PROGRESS', 'IN-PROGRESS'),
        ('CHANGES-REQUIRED', 'CHANGES-REQUIRED')
    )
    chapter_id = models.AutoField(primary_key=True)
    chapter_no = models.FloatField(blank=True, null=True)
    chapter_name = models.CharField(max_length=500)
    no_of_parts = models.CharField(max_length=10)
    chapter_code = models.CharField(max_length=100, default=1, blank=True, null=True)
    status = models.CharField(choices=status_options, default='IN-PROGRESS', max_length=100)
    subject_id_id = models.IntegerField()
    user_id_id = models.IntegerField()
    board_id_id = models.IntegerField()
    district_id_id = models.IntegerField()
    medium_id_id = models.IntegerField()
    class_id_id = models.IntegerField()
    creator_credits = models.JSONField(default=dict)
    updated_by_id = models.IntegerField()
    is_deleted = models.BooleanField(default=False)
    is_grammar_generated = models.BooleanField(default=False)
    study_time = models.BigIntegerField(default=3600000)

    class Meta:
        managed = False
        db_table = "Students_App_chapter"

    @property
    def board_name(self):
        return Boards.objects.using('mysql-master-db').get(board_id=self.board_id_id).board_name

    @property
    def chapter_created_by(self):
        try:
            user_name = AdminProfile.objects.using('mysql-master-db').get(user_id_id=self.user_id_id).full_name
        except:
            user_name = ""
        return user_name

    @property
    def status_change_by(self):
        try:
            updated_by = AdminProfile.objects.using('mysql-master-db').get(user_id_id=self.updated_by_id).full_name
        except:
            updated_by = ""
        return updated_by

    @property
    def class_name(self):
        return Classes.objects.using('mysql-master-db').get(class_id=self.class_id_id).class_name

    @property
    def district_name(self):
        return District.objects.using('mysql-master-db').get(district_id=self.district_id_id).district_name

    @property
    def medium_name(self):
        return Medium.objects.using('mysql-master-db').get(medium_id=self.medium_id_id).medium_name

    @property
    def subject_name(self):
        return Subjects.objects.using('mysql-master-db').get(subject_id=self.subject_id_id).subject_name


class ChapterParts(BaseModel):
    json_update_status_options = (
        ('IN-PROGRESS', 'IN-PROGRESS'),
        ('COMPLETED', 'COMPLETED'),
        ('NOT-COMPLETED', 'NOT-COMPLETED'),
        ('ERROR', 'ERROR')
    )
    part_id = models.AutoField(primary_key=True)
    part_name = models.CharField(max_length=100)
    tags = models.CharField(max_length=1000, default="", blank=True, null=True)
    sequence = models.CharField(max_length=10, default="", blank=True, null=True)
    chapter_id = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='parts')
    user_id_id = models.IntegerField()
    is_deleted = models.BooleanField(default=False)
    json_update_status = models.CharField(choices=json_update_status_options, default='NOT-COMPLETED', max_length=100)

    class Meta:
        managed = False
        db_table = "Students_App_chapterparts"


class ContentUrl(BaseModel):
    content_id = models.AutoField(primary_key=True)
    content = models.CharField(max_length=500, default=1, null=True, blank=True)
    part_id = models.ForeignKey(ChapterParts, on_delete=models.CASCADE)
    chapter_id = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "Students_App_contenturl"


class Category(BaseModel):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "content_category"

    def __str__(self):
        return self.name


def media_upload_path(instance, filename):
    """
    Method used to generate the Path for upload the file.
    :param instance:
    :param filename:
    :return:
    """
    file_name = str(int(time.time())) + filename
    return f"media/{instance.media_type}/" + instance.name + f"_{file_name}"


class Media(BaseModel):
    media_type_choice = (
        ('IMAGE', 'IMAGE'),
        ('AUDIO', 'AUDIO'),
        ('VIDEO', 'VIDEO'),
        ('PDF', 'PDF'),
        ('PPT', 'PPT'),
        ('LOTTY FILE', 'LOTTY FILE'),
        ('GIF', 'GIF')
    )
    media_id = models.AutoField(primary_key=True)
    category = models.ManyToManyField(Category, blank=True, related_name='media_category')
    media_type = models.CharField(choices=media_type_choice, default='IMAGE', max_length=100)
    tags = models.CharField(max_length=500, null=True)
    name = models.CharField(max_length=500)
    used_in = models.JSONField(null=True)
    file = models.FileField(upload_to=media_upload_path)
    file_url = models.CharField(max_length=500, null=True)
    user_id = models.IntegerField(null=True)
    classes = models.CharField(max_length=250, null=True)

    class Meta:
        managed = False
        db_table = "content_media"


class ChapterRating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    student_id_id = models.IntegerField()
    chapter_id = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='chapter_ratings')
    rating = models.IntegerField(default=0)
    review = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "Students_App_chapterrating"


class RequestStatus(BaseModel):
    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=255)
    user_id = models.IntegerField()
    request_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    data = models.JSONField(default=dict)
    chapter_id = models.IntegerField(default=0)
    error = models.JSONField(default=dict)

    class Meta:
        managed = False
        db_table = "content_requeststatus"


class StudentProfile(models.Model):
    gen_types = (
        ('MALE', 'MALE'),
        ('FEMALE', 'FEMALE'),
        ('OTHER', 'OTHER'),
    )
    student_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    user_name = models.CharField(max_length=250, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(choices=gen_types, max_length=50, blank=True, null=True)
    profilepic_url = models.CharField(max_length=500, blank=True, null=True)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE, blank=True, null=True, related_name='student_user')
    state_id_id = models.IntegerField()
    district_id = models.ForeignKey(District, on_delete=models.CASCADE, blank=True, null=True)
    board_id = models.ForeignKey(Boards, on_delete=models.CASCADE, blank=True, null=True)
    class_id = models.ForeignKey(Classes, on_delete=models.CASCADE, blank=True, null=True)
    medium_id = models.ForeignKey(Medium, on_delete=models.CASCADE, blank=True, null=True)
    student_state_id_id = models.IntegerField()
    student_district_id_id = models.IntegerField()
    student_block_id_id = models.IntegerField()
    school_id_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    app_version = models.CharField(max_length=45, null=True)

    class Meta:
        managed = False
        db_table = "Students_App_studentprofile"


class PassageBank(BaseModel):
    id = models.AutoField(primary_key=True)
    signature = models.CharField(max_length=255)
    grammar_data= models.JSONField()
    question_list = models.JSONField()

    class Meta:
        managed = False
        db_table = "content_passagebank"


class ElementData(models.Model):
    
    unique_id = models.CharField(max_length=255, unique=True)
    chapter_id = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    part_id = models.ForeignKey(ChapterParts, on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    time = models.FloatField()
    word_count = models.IntegerField(null=True, blank=True)
    points = models.IntegerField()

    class Meta:
        managed = False
        db_table = "content_elementdata"


class LearningElement(BaseModel):
    element_id = models.AutoField(primary_key=True)
    classes = models.IntegerField()
    subject = models.IntegerField()
    learning_element = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "mcq_learningelement"

    def __str__(self):
        return self.learning_element

    @property
    def class_name(self):
        return Classes.objects.using('mysql-master-db').get(class_id=self.classes).class_name

    @property
    def subject_name(self):
        return Subjects.objects.using('mysql-master-db').get(subject_id=self.subject).subject_name


class Mcq(BaseModel):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="mcq_chapter")
    part = models.ForeignKey(ChapterParts, on_delete=models.CASCADE, related_name="mcq_parts")
    created_by = models.IntegerField()
    question_url = models.CharField(max_length=500, null=True)
    max_marks = models.IntegerField()
    is_deleted = models.BooleanField(default=False)
    test_no = models.IntegerField(blank=True, null=True)
    test_name = models.CharField(max_length=255, blank=True, null=True)
    test_time = models.CharField(max_length=255, blank=True, null=True)
    negative_mark = models.CharField(max_length=255, blank=True, null=True)
    learning_element = models.ForeignKey(LearningElement, on_delete=models.CASCADE, blank=True,
                                         null=True, related_name="mcq_learning_element")
    
    class Meta:
        managed = False
        db_table = "mcq_mcq"

    def __str__(self):
        return self.test_name or ''


class McqQuestions(BaseModel):
    que_id = models.CharField(max_length=255, blank=True, null=True)
    mcq = models.ForeignKey(Mcq, on_delete=models.CASCADE, related_name="mcq_set", null=True)
    class_id_id = models.IntegerField()
    subject_id_id = models.IntegerField()
    medium_id_id = models.IntegerField()
    question = models.CharField(max_length=255, blank=True, null=True)
    questionType = models.CharField(max_length=255, blank=True, null=True)
    answers = models.CharField(max_length=255, blank=True, null=True)
    correctAnswer = models.CharField(max_length=255, blank=True, null=True)
    point = models.FloatField()
    messageForCorrectAnswer = models.CharField(max_length=255, blank=True, null=True)
    messageForIncorrectAnswer = models.CharField(max_length=255, blank=True, null=True)
    explanation = models.CharField(max_length=500, blank=True, null=True)
    explanationLink = models.CharField(max_length=255, blank=True, null=True)
    quizTitle = models.CharField(max_length=255, blank=True, null=True)
    time = models.CharField(max_length=255, blank=True, null=True)
    learning_element = models.ForeignKey(LearningElement, on_delete=models.CASCADE, blank=True,
                                         null=True, related_name="mcq_question_le")
    questionVideo = models.CharField(max_length=255, blank=True, null=True)
    questionAUDIO = models.CharField(max_length=255, blank=True, null=True)
    questionPic = models.CharField(max_length=255, blank=True, null=True)
    topic = models.CharField(max_length=255, blank=True, null=True)
    ai_generated = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "mcq_mcqquestion"

    def set_answers(self, ans):
        self.answers = json.dumps(ans)

    def get_answers(self):
        return json.loads(self.answers)

    def __str__(self):
        return self.question or ''


class McqFirstAttempt(BaseModel):
    """
        Model for store the first attempts records of the mcq test.
    """
    mcq = models.ForeignKey(Mcq, on_delete=models.CASCADE, related_name="mcq_test_best")
    student_id = models.IntegerField()
    marks = models.IntegerField()
    time = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20)
    part = models.ForeignKey(ChapterParts, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    state_id = models.IntegerField()
    district_id = models.IntegerField()
    block_id = models.IntegerField()
    student_class_id = models.IntegerField()
    subject_id = models.IntegerField()
    medium_id = models.IntegerField()
    board_id = models.IntegerField()
    school_id = models.IntegerField()
    attempt_no = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "mcq_mcqfirstattempt"


class McqBestAttempt(BaseModel):
    """
    Model for store the best attempts records of the mcq test.
    """
    mcq = models.ForeignKey(Mcq, on_delete=models.CASCADE, related_name="mcq_test_first")
    student_id = models.IntegerField()
    marks = models.IntegerField()
    time = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20)
    part = models.ForeignKey(ChapterParts, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    state_id = models.IntegerField()
    district_id = models.IntegerField()
    block_id = models.IntegerField()
    student_class_id = models.IntegerField()
    subject_id = models.IntegerField()
    medium_id = models.IntegerField()
    board_id = models.IntegerField()
    school_id = models.IntegerField()
    attempt_no = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "mcq_mcqbestattempt"


class McqTopics(BaseModel):
    mcq_topic_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_id = models.IntegerField()
    subject_id = models.IntegerField()
    medium_id = models.IntegerField(null=True)
    class_name = models.CharField(max_length=255)
    subject_name = models.CharField(max_length=255)
    chapter_name = models.CharField(max_length=255)
    topic_name = models.CharField(max_length=255)
    is_generated = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "mcq_mcqtopics"

    def __str__(self):
        return self.topic_name or ''


class Devices(models.Model):
    device_id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(max_length=255, null=True, unique=True)
    arn = models.CharField(max_length=255, null=True, unique=True)
    active = models.BooleanField(default=True)
    user = models.OneToOneField(Users, on_delete=models.DO_NOTHING, related_name='mobile_device')

    class Meta:
        managed = False
        db_table = 'Students_App_devices'

#---------------------------------models for student activites-----------------------------------#


class DjongoBaseModel(models.Model):
    """
    Base Model with created and updated time fields.
    """
    _id = djongo_models.ObjectIdField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ReelsAttempt(DjongoBaseModel):
    student_id = models.IntegerField()
    subject_id = models.IntegerField()
    class_id = models.IntegerField()
    ai_generated = models.BooleanField()
    total_reels = models.IntegerField()
    correct = models.IntegerField()
    incorrect = models.IntegerField()
    points = models.IntegerField(null=True)
    time = models.BigIntegerField()

    def calculate_points(self):
        """
        Giving 1 point per correct answer
        required field = correct
        :return:
        """
        points_per_correct = 1
        self.points = self.correct * points_per_correct
        self.save()


class StudentElementTime(DjongoBaseModel):
    user_id = models.IntegerField()
    student_id = models.IntegerField()
    element_id = models.CharField(max_length=255)
    element_type = models.CharField(max_length=50)
    time = models.IntegerField()
    points = models.IntegerField()
    class_id = models.IntegerField()
    subject_id = models.IntegerField()
    chapter_id = models.IntegerField()
    part_id = models.IntegerField()
    

class PartsProgress(DjongoBaseModel):
    user_id = models.IntegerField()
    student_id = models.IntegerField()
    chapter_id = models.IntegerField()
    part_id = models.IntegerField()
    subject_id = models.IntegerField()
    class_id = models.IntegerField()
    time = models.IntegerField()
    points = models.IntegerField()
    percentage = models.FloatField()


class ChapterProgress(DjongoBaseModel):
    user_id = models.IntegerField()
    student_id = models.IntegerField()
    chapter_id = models.IntegerField()
    subject_id = models.IntegerField()
    class_id = models.IntegerField()
    time = models.IntegerField()
    points = models.IntegerField()
    percentage = models.FloatField()


class StudentTimePoints(DjongoBaseModel):
    point_activity = models.CharField(max_length=255)
    points = models.IntegerField()
    time = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField()
    student_id = models.IntegerField()
    school_id = models.IntegerField()
    class_id = models.IntegerField()
    medium_id = models.IntegerField()


class Diamond(DjongoBaseModel):
    activity = models.CharField(max_length=255)
    diamond = models.IntegerField()
    user_id = models.IntegerField()
    student_id = models.IntegerField()
    school_id = models.IntegerField()
    class_id = models.IntegerField()
    medium_id = models.IntegerField()


MILESTONES_CHOICES = [
        ('Total Chapter', 'Total Chapter'),
        ('Total Reels Attempts', 'Total Reels Attempts'),
        # ('Total Points Earn', 'Total Points Earn'),
        # ('Daily Open', 'Daily Open')
    ]


class Milestones(DjongoBaseModel):
    sn = models.PositiveIntegerField(unique=True, blank=True, null=True)
    milestone = models.CharField(max_length=255, choices=MILESTONES_CHOICES)
    medium_id = models.IntegerField(null=True, blank=True)
    class_id = models.IntegerField(null=True, blank=True)
    subject_id = models.IntegerField(null=True, blank=True)
    value = models.IntegerField()
    reward = models.IntegerField(null=True, blank=True)
    diamond = models.IntegerField(null=True, blank=True)
    reward_message = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    lotti_fetch_key = djongo_models.JSONField(null=True, blank=True)
    description = models.TextField()
    is_deleted = djongo_models.BooleanField(default=False)

    def delete(self, **kwargs):
        self.is_deleted = True
        self.save()


class StudentMilestone(DjongoBaseModel):
    student_id = models.IntegerField()
    user_id = models.IntegerField()
    reward = models.IntegerField()
    milestone_type = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    milestone = djongo_models.ForeignKey(Milestones, on_delete=models.CASCADE, related_name='student_milestone')
    completed_at = models.DateTimeField(null=True, blank=True)


class DailyReward(DjongoBaseModel):
    reward_day = models.IntegerField(unique=True)
    reward_type = models.CharField(max_length=50)
    points = models.IntegerField(null=True)
    diamond = models.IntegerField(null=True)
    physical_gift_available = models.BooleanField(default=False)
    google_form_link = models.TextField(null=True)


class DailyStreak(DjongoBaseModel):
    student_id = models.IntegerField()
    user_id = models.IntegerField()
    streak_count = models.IntegerField(default=0)
    last_login_date = models.DateField(null=True)
    reward = djongo_models.ForeignKey(DailyReward, on_delete=models.CASCADE, null=True,
                                      related_name='student_daily_reward')

