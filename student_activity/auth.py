import rest_framework
import jwt
import datetime

from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework import exceptions
from django.core.cache import cache
from data_points.models import Users
from student_activity import settings


class JWTAuthentication(BaseAuthentication):
    """
    Custom Authentication class for the JWT Authentication from the master db.
    override the authenticate method for the check user from master db.
    """

    def authenticate(self, request):
        if isinstance(request, rest_framework.request.Request):
            authorization = request.META.get('HTTP_AUTHORIZATION', None)
        else:
            authorization = request.request.META.get('HTTP_AUTHORIZATION', None)
        if authorization is None:
            raise exceptions.AuthenticationFailed('Authentication credentials were not provided.')
        else:
            authorization = authorization.replace('JWT', '')
            if authorization.startswith("b"):
                new_authorization = ""
                char = "''"
                for character in char:
                    authorization = authorization.replace(character, '')
                for i in range(len(authorization)):
                    if i != 0:
                        new_authorization = new_authorization + authorization[i]
                authorization = new_authorization

            try:
                payload = jwt.decode(authorization, settings.SECRET_KEY,
                                     algorithms=['HS256', ], options={"verify_exp": False},)
            except:
                raise exceptions.AuthenticationFailed('Authentication token invalid')

            userid = payload['user_id']

            if cache.get(userid):
                user = cache.get(userid)
            else:
                try:
                    user = Users.objects.using('mysql-master-db').get(user_id=userid)
                    cache.set(userid, user, datetime.timedelta(hours=12).total_seconds())
                except Exception as err:
                    raise exceptions.AuthenticationFailed('User not found.')
            token = user.token
            if authorization in (token, token[2:-1]):
                return user, None
            else:
                raise exceptions.AuthenticationFailed('Authentication token invalid')


class AllowContentWriting(BasePermission):
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if view.action in ['get_student_milestone', 'get_milestone']:
            return True
        elif request.user.user_type in ['ADMIN', 'SUPERADMIN', 'CONTENT-WRITER']:
            return True
        return False


class StudentPermission(BasePermission):
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        if request.user.user_type in ['STUDENT']:
            return True
        return False


class AllowedToAll(BasePermission):
    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

