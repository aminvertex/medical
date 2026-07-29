from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render
from ninja.errors import HttpError
from ninja.security import SessionAuth

from .models import User


class RoleSessionAuth(SessionAuth):
    """Session authentication plus an explicit role check.

    ``SessionAuth`` is implemented as cookie authentication. Its constructor
    initializes CSRF and OpenAPI metadata, so subclasses must call ``super``.
    Django Ninja also passes the session-cookie value to ``authenticate``.

    Anonymous requests receive 401. Authenticated users with a wrong role
    receive 403, which keeps authentication and authorization distinguishable.
    """

    def __init__(self, *roles: str, csrf: bool = True):
        super().__init__(csrf=csrf)
        self.roles = frozenset(roles)

    def authenticate(self, request, key=None):
        user = super().authenticate(request, key)
        if not user:
            return None
        if user.is_superuser or user.role in self.roles:
            return user
        raise HttpError(403, "شما اجازه دسترسی به این بخش را ندارید.")


student_auth = RoleSessionAuth(User.Role.STUDENT, User.Role.INSTRUCTOR, User.Role.ADMIN)
instructor_auth = RoleSessionAuth(User.Role.INSTRUCTOR, User.Role.ADMIN)
admin_auth = RoleSessionAuth(User.Role.ADMIN)


def role_required(*roles):
    """Protect template views with the same role rules used by the API."""

    allowed_roles = frozenset(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return render(request, "errors/403.html", status=403)

        return wrapper

    return decorator
