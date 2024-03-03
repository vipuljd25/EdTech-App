from rest_framework import serializers
from .models import (ReelsAttempt, StudentElementTime, PartsProgress, StudentTimePoints,
                     Milestones, ChapterProgress, StudentMilestone, McqFirstAttempt, McqBestAttempt,
                     Diamond, DailyStreak, DailyReward)


class ReelsAttemptSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReelsAttempt
        fields = "__all__"


class StudentElementTimeSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentElementTime
        fields = "__all__"


class PartsProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = PartsProgress
        fields = "__all__"


class ChapterProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChapterProgress
        fields = "__all__"


class StudentTimePointsSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudentTimePoints
        fields = "__all__"


class MilestonesSerializer(serializers.ModelSerializer):
    lotti_fetch_key = serializers.JSONField(required=False, default={})
    achieved = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Milestones
        fields = "__all__"

    def get_achieved(self, obj):
        count = obj.student_milestone.count()
        return count


class StudentMilestonesSerializer(serializers.ModelSerializer):
    lotti_fetch_key = serializers.JSONField(read_only=True)
    completed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Milestones
        fields = "__all__"

    def get_completed(self, obj):
        student_id = self.context.get('student_id')
        exist = StudentMilestone.objects.filter(student_id=int(student_id), milestone_id=obj._id).exists()
        return exist


class McqFirstAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = McqFirstAttempt
        fields = "__all__"


class McqBestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = McqBestAttempt
        fields = "__all__"


class DiamondSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diamond
        fields = "__all__"


class DailyStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStreak
        fields = "__all__"


class DailyRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReward
        fields = "__all__"

