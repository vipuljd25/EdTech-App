from rest_framework import serializers

from data_points.models import Schools
from .models import Nudges, NudgesConfig, StudentNudges, Templates


class NudgesConfigSerializer(serializers.ModelSerializer):
    parameters = serializers.JSONField(required=False, default={})
    nudges_info = serializers.JSONField(required=False, default={})
    input_fields = serializers.JSONField(required=False, default={})
    variables = serializers.JSONField(required=False, default={})

    class Meta:
        model = NudgesConfig
        fields = '__all__'


class NudgesSerializer(serializers.ModelSerializer):
    nudges_info = serializers.JSONField(required=False, default={})
    school_id = serializers.JSONField(required=False, default={})
    school_list = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Nudges
        fields = '__all__'

    def get_school_list(self, obj):
        school_ids = obj.school_id
        school_list = []
        if school_ids:
            school_list = Schools.objects.filter(school_id__in=school_ids).values('school_id', 'school_name')
        return school_list


class StudentNudgesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentNudges
        fields = '__all__'


class TemplatesSerializer(serializers.ModelSerializer):
    variables = serializers.JSONField(required=False, default=[])

    class Meta:
        model = Templates
        fields = '__all__'
