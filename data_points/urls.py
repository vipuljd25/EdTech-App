from data_points import views
from rest_framework import routers


router = routers.DefaultRouter()

router.register(r'api/reels_attempt', views.ReelsAttemptViewSet, basename='reels_attempt')
router.register(r'api/student_element_time', views.StudentElementTimeViewset, basename='student_element_time')
router.register(r'api/parts_progress', views.PartsProgressViewset, basename='parts_progress')
router.register(r'api/student_time_points', views.StudentTimePointsViewSet, basename='student_time_points')
router.register(r'api/milestone', views.MilestonesViewSet, basename='milestone')
router.register('api/attempts', views.StudentMcqFirstAttemptViewSet, basename='mcq_first_attempt')
router.register('api/diamond', views.DiamondViewSet, basename='student_diamonds')
router.register('api/daily_streak', views.DailyStreakViewSet, basename='student_diamonds')

urlpatterns = router.urls
