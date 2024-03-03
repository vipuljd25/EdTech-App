from django.contrib import admin
from .models import ChallengeConfig, AdvanceFilterConfig

@admin.register(ChallengeConfig)
class ChallengeConfigAdmin(admin.ModelAdmin):
    list_display = ['_id', 'challenges', 'sub_challenges', 'parameters', 'components', 'comparison_operator', 'unit', 'created_at', 'updated_at']
    search_fields = ['challenges', 'sub_challenges']

@admin.register(AdvanceFilterConfig)
class AdvanceFilterConfigAdmin(admin.ModelAdmin):
    list_display = ['user_type', 'timeframe', 'value', 'comparison_operator']
    search_fields = ['user_type']