from django.db import models
from djongo import models as djongo_models


class DjongoBaseModel(models.Model):
    """
    Base Model with created and updated time fields.
    """
    _id = djongo_models.ObjectIdField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NudgesConfig(DjongoBaseModel):
    nudges_type = models.CharField(max_length=255)
    parameters = djongo_models.JSONField()
    nudges_info = djongo_models.JSONField()
    input_fields = djongo_models.JSONField()
    variables = djongo_models.JSONField()


class Templates(DjongoBaseModel):
    template_name = models.CharField(max_length=255)
    nudges_type = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    message = models.TextField(null=True, blank=True)
    platform = models.CharField(max_length=255)
    variables = djongo_models.JSONField(null=True, blank=True)


class Nudges(DjongoBaseModel):
    nudges_title = models.CharField(max_length=255)
    sn_no = models.IntegerField()
    nudges_type = models.CharField(max_length=255)
    state_id = models.IntegerField(blank=True, null=True)
    district_id = models.IntegerField(blank=True, null=True)
    block_id = models.IntegerField(blank=True, null=True)
    medium_id = models.IntegerField(blank=True, null=True)
    class_id = models.IntegerField(blank=True, null=True)
    school_id = djongo_models.JSONField()
    nudges_info = djongo_models.JSONField(blank=True, null=True)
    trigger_parameter = models.CharField(max_length=255, blank=True, null=True)
    trigger_key = models.CharField(max_length=255, blank=True, null=True)
    initial_trigger_value = models.IntegerField(blank=True, null=True)
    final_trigger_value = models.IntegerField(blank=True, null=True)
    check_parameter = models.CharField(max_length=255, blank=True, null=True)
    check_condition = models.CharField(max_length=255)
    timeframe_duration = models.IntegerField()
    repeat_time_duration = models.IntegerField(blank=True, null=True)
    repeat = models.BooleanField(default=False)
    repeat_count = models.IntegerField(blank=True, null=True)
    notification_platform = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    image = models.CharField(max_length=255)
    templates = models.CharField(max_length=255, null=True, blank=True)
    messages = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)


class StudentNudges(DjongoBaseModel):
    student_id = models.IntegerField()
    user_id = models.IntegerField()
    nudges = djongo_models.ForeignKey(Nudges, on_delete=models.CASCADE, related_name='student_nudges')
    last_sent_at = models.DateTimeField(null=True)
    next_sent_at = models.DateTimeField()
    sent_count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
