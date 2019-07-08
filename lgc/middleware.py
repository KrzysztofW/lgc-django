from django.utils.deprecation import MiddlewareMixin
from users import models as user_models
from django.core.exceptions import PermissionDenied
import re, os, logging
from django.db import connection

log = logging.getLogger('sql')

allowed_urls = [
    '/', '/favicon.ico', '/user/login',  '/user/auth/', '/user/logout/',
    '/user/profile/', '/user/profile-pw-reset/',
    '/user/delete-profile/',
]

class UserRolesCheck(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request.user, 'role'):
            return

        if request.user.role in user_models.get_internal_roles():
            return

        for i in allowed_urls:
            if (request.path == i or request.path == '/en' + i or
                request.path == '/fr' + i):
                return

        if request.user.role == user_models.ROLE_EMPLOYEE:
            if re.search("^/((en)|(fr))/emp/.*$", request.path) == None:
                raise PermissionDenied
            return

        if request.user.role in user_models.get_hr_roles():
            if (re.search("^/((en)|(fr))/hr/.*$", request.path) == None and
                re.search("^/((en)|(fr))/file/.*", request.path) == None):
                raise PermissionDenied
            return

        raise PermissionDenied

class SqlLogger(MiddlewareMixin):
    def process_response(self, request, response):
        if not hasattr(request.user, 'first_name'):
            return response

        for q in connection.queries:
            if q['sql'] == None:
                continue

            if (q['sql'].startswith('UPDATE ') or
                q['sql'].startswith('INSERT ') or
                q['sql'].startswith('DELETE ')):
                log.info('%s %s (%d): %s\n', request.user.first_name,
                         request.user.last_name, request.user.id, q['sql'])
        return response
