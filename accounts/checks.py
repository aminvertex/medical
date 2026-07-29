import inspect

from django.core.checks import Error, register

from .security import admin_auth, instructor_auth, student_auth


@register()
def role_session_auth_checks(app_configs, **kwargs):
    """Fail ``manage.py check`` if custom Ninja session auth regresses."""

    errors = []
    for name, auth in (
        ("student_auth", student_auth),
        ("instructor_auth", instructor_auth),
        ("admin_auth", admin_auth),
    ):
        if not hasattr(auth, "csrf"):
            errors.append(
                Error(
                    f"{name} فاقد ویژگی csrf است؛ سازنده SessionAuth اجرا نشده است.",
                    id="accounts.E001",
                )
            )
        parameters = list(inspect.signature(auth.authenticate).parameters.values())
        if len(parameters) < 2 or parameters[0].name != "request":
            errors.append(
                Error(
                    f"امضای authenticate در {name} با Django Ninja سازگار نیست.",
                    hint="امضای متد باید authenticate(request, key=None) باشد.",
                    id="accounts.E002",
                )
            )
    return errors
