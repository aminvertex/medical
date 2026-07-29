from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import render
from ninja.errors import HttpError
from ninja.security import SessionAuth

from .models import User


class RoleSessionAuth(SessionAuth):
    """Session authentication plus an explicit role check.

    Anonymous requests receive 401 from Django Ninja. Authenticated users with a
    wrong role receive 403, which is the distinction required for the project.
    """

    def __init__(self, *roles: str):
        self.roles = set(roles)
        self.csrf = True  # Add csrf attribute for Django Ninja compatibility

    def authenticate(self, request):
        user = super().authenticate(request)
        if not user:
            return None
        if user.is_superuser or user.role in self.roles:
            return user
        raise HttpError(403, "شما اجازه دسترسی به این بخش را ندارید.")


student_auth = RoleSessionAuth(User.Role.STUDENT, User.Role.INSTRUCTOR, User.Role.ADMIN)
instructor_auth = RoleSessionAuth(User.Role.INSTRUCTOR, User.Role.ADMIN)
admin_auth = RoleSessionAuth(User.Role.ADMIN)


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return render(request, "errors/403.html", status=403)
        return wrapper
    return decorator
