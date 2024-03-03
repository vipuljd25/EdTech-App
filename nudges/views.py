import django_filters
from bson import ObjectId
from rest_framework import viewsets, filters, status
from rest_framework.response import Response

from nudges.filters import NudgesFilters
from student_activity.auth import JWTAuthentication, AllowContentWriting
from .models import Nudges, NudgesConfig, StudentNudges, Templates
from .serializers import NudgesSerializer, NudgesConfigSerializer, StudentNudgesSerializer, TemplatesSerializer


class NudgesConfigViewSet(viewsets.ModelViewSet):
    queryset = NudgesConfig.objects.all()
    serializer_class = NudgesConfigSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ["nudges_type"]
    http_method_names = ['get', 'post']
    ordering_fields = '__all__'

    def list(self, request, *args, **kwargs):
        """
        if nudges_type_list == True, then give unique list of nudges type
        """

        if request.query_params.get('nudges_type_list'):
            unique_nudges_types = NudgesConfig.objects.values_list('nudges_type', flat=True).distinct()
            return Response({"nudges_type": unique_nudges_types})
        else:
            return super().list(request, *args, **kwargs)


class NudgesViewSet(viewsets.ModelViewSet):
    queryset = Nudges.objects.all()
    serializer_class = NudgesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ["nudges_type", "notification_platform", "active"]
    filterset_class = NudgesFilters
    search_fields = ['nudges_title']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    ordering_fields = '__all__'

    def get_object(self):
        try:
            object_id = ObjectId(self.kwargs['pk'])
            return Nudges.objects.get(_id=object_id)
        except Exception as e:
            return Response({"message": "Failed", "status": status.HTTP_400_BAD_REQUEST,
                             "response": f"get_object error, Error: {e}"})

    def create(self, request, *args, **kwargs):
        # add serial no
        latest_nudge = Nudges.objects.order_by('-sn_no').first()
        if latest_number := latest_nudge.sn_no:
            serial_number = latest_number + 1
        else:
            serial_number = 1
        request.data['sn_no'] = serial_number
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentNudgesViewSet(viewsets.ModelViewSet):
    queryset = StudentNudges.objects.all()
    serializer_class = StudentNudgesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = []
    http_method_names = ['get', 'post']
    ordering_fields = '__all__'


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = Templates.objects.all()
    serializer_class = TemplatesSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowContentWriting]
    filter_backends = [filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter]
    filter_fields = ['nudges_type', 'active', 'platform']
    http_method_names = ['get', 'post']
    ordering_fields = '__all__'

