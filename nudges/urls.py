from nudges import views
from rest_framework import routers


router = routers.DefaultRouter()

router.register(r'api/nudges_config', views.NudgesConfigViewSet, basename='nudges_config')
router.register(r'api/nudges', views.NudgesViewSet, basename='nudges')
router.register(r'api/student_nudges', views.StudentNudgesViewSet, basename='student_nudges')
router.register(r'api/templates', views.TemplateViewSet, basename='templates')

urlpatterns = router.urls
