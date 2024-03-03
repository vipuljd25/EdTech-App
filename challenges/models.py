from django.db import models
from djongo import models as djongo_models


class BaseModel(models.Model):
    """
    Base Model with created and updated time fields.
    """
    _id = djongo_models.ObjectIdField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ChallengeConfig(BaseModel):
    challenges = models.CharField(max_length=255)
    sub_challenges = models.CharField(max_length=255)
    parameters = models.JSONField()
    components = models.JSONField(blank=True, null=True)
    comparison_operator = models.JSONField()
    unit = models.JSONField()
    color_code = models.CharField(max_length=255, null=True)


class AdvanceFilterConfig(BaseModel):
    user_type = models.CharField(max_length=255)
    timeframe = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    actual_value = models.IntegerField(blank=True, null=True)
    comparison_operator = models.JSONField(blank=True, null=True)


class ChallengeDataManager(models.Manager):
    """
    Overwrite the get_queryset method for filtering active subjects record.
    """
    def get_queryset(self):
        return super(ChallengeDataManager, self).get_queryset().filter(is_deleted__in=[False])


class ChallengeAllDataManager(models.Manager):
    """
    Overwrite the get_queryset method for filtering active subjects record.
    """
    def get_queryset(self):
        return super(ChallengeAllDataManager, self).get_queryset()


class ChallengeData(BaseModel):
    """
    Model for challenges which are created by super admin.
    """
    STATUS_CHOICES = [
        ('DRAFT', 'DRAFT'),
        ('ACTIVE', 'ACTIVE'),
        ('EXPIRED', 'EXPIRED'),
        ('PUBLISHED', 'PUBLISHED')
    ]
    challenge_id = models.IntegerField(unique=True)
    challenge_title = models.CharField(max_length=255)
    district_id = models.IntegerField(blank=True, null=True)  # syllabus id
    board_id = models.IntegerField(blank=True, null=True)
    class_id = models.IntegerField(blank=True, null=True)
    medium_id = models.IntegerField(blank=True, null=True)
    school_id = djongo_models.JSONField(default=[])  # will need an empty list, It won't take Null
    student_state_id = models.IntegerField(blank=True, null=True)
    student_district_id = models.IntegerField(blank=True, null=True)
    student_block_id = models.IntegerField(blank=True, null=True)
    advance_filter = djongo_models.JSONField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    reward_points = models.PositiveIntegerField(null=True, blank=True)
    diamond = models.IntegerField(null=True, blank=True)
    reward_message = models.CharField(max_length=200)
    challenge_info = djongo_models.JSONField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='DRAFT')
    challenge_display = djongo_models.JSONField()
    after_success = djongo_models.JSONField()
    created_by = models.IntegerField()
    updated_by = models.IntegerField()
    is_deleted = models.BooleanField(default=False, null=True, blank=True)
    filter_condition = djongo_models.JSONField(default={})
    advance_filter_condition = djongo_models.JSONField(default={})

    objects = ChallengeDataManager()
    all_objects = ChallengeAllDataManager()

    def delete(self, **kwargs):
        self.is_deleted = True
        self.save()


class StudentChallengeData(BaseModel):
    """
    Model which will used for the store student challenges data.
    created date will also use as sent date.
    """
    STATUS_CHOICES = [
        ('SENT', 'SENT'),
        ('ACCEPTED', 'ACCEPTED'),
        ('COMPLETED', 'COMPLETED'),
    ]
    CHALLENGE_STATUS = [
        ('EXPIRED', 'EXPIRED'),
        ('ACTIVE', 'ACTIVE'),
    ]
    challenge_status = models.CharField(max_length=50, choices=CHALLENGE_STATUS, default='ACTIVE')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='SENT')
    student_id = models.IntegerField()
    user_id = models.IntegerField()
    accepted_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    challenge = djongo_models.ForeignKey(ChallengeData, on_delete=models.CASCADE, related_name='student_challenge')
    progress = models.IntegerField()
