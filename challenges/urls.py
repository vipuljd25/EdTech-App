from challenges import views
from rest_framework import routers


router = routers.DefaultRouter()

router.register(r'api/challenge_config', views.ChallengeConfigViewSet, basename='challenge_config')
router.register(r'api/advancefilter_config', views.AdvanceFilterConfigViewSet, basename='advancefilter_config')
router.register(r'api/challenge_data', views.ChallengeDataViewSet, basename='challenge_data')
router.register(r'api/student_challenge_data', views.StudentChallengeDataViewSet, basename='student_challenge_data')

urlpatterns = router.urls