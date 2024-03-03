"""
URL configuration for student_activity project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from student_activity import settings
from data_points import views as data_point_views

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="Your API description",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="contact@yourapp.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('student_activity/api/admin/', admin.site.urls),
    path('api/health/', data_point_views.health),
    path('student_activity/', include('data_points.urls')),
    path('student_activity/', include('challenges.urls')),
    path('student_activity/', include('nudges.urls')),
    re_path(r'^student_activity/api/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0),
          name='schema-json'),
    re_path(r'^student_activity/api/swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
          name='schema-swagger-ui'),
    re_path(r'^student_activity/api/redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

