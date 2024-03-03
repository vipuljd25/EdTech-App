import json
from rest_framework import serializers
from challenges.models import ChallengeConfig, ChallengeData, AdvanceFilterConfig, StudentChallengeData
from data_points.models import Schools


class ChallengeConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeConfig
        fields = '__all__'


class AdvanceFilterConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceFilterConfig
        fields = '__all__'


class ChallengeDataSerializer(serializers.ModelSerializer):
    challenge_info = serializers.JSONField()
    challenge_display = serializers.JSONField()
    after_success = serializers.JSONField()
    filter_condition = serializers.JSONField(read_only=True)
    advance_filter_condition = serializers.JSONField(read_only=True)
    advance_filter = serializers.JSONField(required=False, default={})
    school_id = serializers.JSONField(default=[])
    sent_count = serializers.SerializerMethodField(read_only=True)
    accepted_count = serializers.SerializerMethodField(read_only=True)
    completed_count = serializers.SerializerMethodField(read_only=True)
    school_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ChallengeData
        fields = [
            '_id', 'challenge_id', 'created_at', 'updated_at', 'challenge_title', 'student_state_id',
            'student_district_id', 'student_block_id', 'district_id', 'medium_id', 'class_id',
            'board_id', 'school_id', 'school_list', 'advance_filter', 'start_date', 'end_date',
            'reward_points', 'reward_message', 'challenge_info', 'status', 'challenge_display',
            'after_success', 'created_by', 'updated_by', 'is_deleted', 'diamond', 'filter_condition',
            'advance_filter_condition', 'sent_count', 'accepted_count', 'completed_count',
        ]

    def get_sent_count(self, obj):
        sent_count = StudentChallengeData.objects.filter(challenge_id=obj._id).count()
        return sent_count

    def get_accepted_count(self, obj):
        accepted_count = StudentChallengeData.objects.filter(challenge_id=obj._id, status="ACCEPTED").count()
        return accepted_count

    def get_completed_count(self, obj):
        completed_count = StudentChallengeData.objects.filter(challenge_id=obj._id, status="COMPLETED").count()
        return completed_count

    def get_school_list(self, obj):
        school_ids = obj.school_id
        school_list = []
        if school_ids:
            school_list = Schools.objects.filter(school_id__in=school_ids).values('school_id', 'school_name')
        return school_list


class ChallengeSerializer(serializers.ModelSerializer):
    challenge_display = serializers.JSONField()
    after_success = serializers.JSONField()

    class Meta:
        model = ChallengeData
        fields = [
            '_id', 'challenge_title', 'start_date', 'end_date', 'reward_points', 'reward_message',
            'status', 'challenge_display', 'after_success', 'diamond'
        ]


class StudentChallengeDataSerializer(serializers.ModelSerializer):
    color_code = serializers.SerializerMethodField(read_only=True)
    challenge = ChallengeSerializer()

    class Meta:
        model = StudentChallengeData
        fields = '__all__'


    def get_color_code(self, obj):
        sub_challenge = obj.challenge.challenge_info.get('sub_challenge')
        val = ChallengeConfig.objects.get(sub_challenges=sub_challenge)
        return val.color_code
