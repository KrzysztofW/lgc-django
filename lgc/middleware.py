from django.utils.deprecation import MiddlewareMixin
from users import models as user_models
from django.core.exceptions import PermissionDenied
import re

public_urls = ['/user/login',  '/user/auth/' ]
allowed_urls = public_urls + [
    '/', '/user/logout/', '/user/profile/',
    '/user/profile-pw-reset/', '/user/delete-profile/',
]

class UserRolesCheck(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request.user, 'role'):
            for i in public_urls:
                if request.path == '/en' + i or request.path == '/fr' + i:
                    return
            raise PermissionDenied

        if request.user.role in user_models.get_internal_roles():
            return

        for i in allowed_urls:
            if request.path == i or request.path == '/en' + i or request.path == '/fr' + i:
                return

        if request.user.role == user_models.EMPLOYEE:
            if re.search("^/((en)|(fr))/emp/.*$", request.path) == None:
                raise PermissionDenied
            return

        if request.user.role in user_models.get_hr_roles():
            if (re.search("^/((en)|(fr))/hr/.*$", request.path) == None and
                re.search("^/((en)|(fr))/file/.*", request.path) == None):
                raise PermissionDenied
            return

        raise PermissionDenied
