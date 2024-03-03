from datetime import timedelta

import django_filters
from nudges.models import Nudges


class NudgesFilters(django_filters.FilterSet):
    # is_deleted = django_filters.BooleanFilter(method='delete_filter')
    created_at = django_filters.DateTimeFilter(method='created_at_filter')

    class Meta:
        model = Nudges
        fields = ["nudges_type", "notification_platform", "active"]

    # def delete_filter(self, queryset, key, value):
    #     return queryset.filter(is_deleted__in=[value])

    def created_at_filter(self, queryset, key, value):
        next_day = value + timedelta(days=1)
        return queryset.filter(created_at__gt=value, created_at__lt=next_day)