from django.db.models.signals import post_save
from django.dispatch import receiver
from data_points.models import (
    PartsProgress, StudentTimePoints,
    StudentElementTime, ReelsAttempt, McqFirstAttempt)



