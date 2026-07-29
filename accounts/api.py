from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.views.decorators.csrf import csrf_protect
from ninja import Router, Schema, Status
from ninja.decorators import decorate_view
from ninja.responses import codes_4xx
from ninja.security import django_auth

from config.schemas import ErrorOut

from .models import User

router = Router(tags=["Authentication"])


class RegisterIn(Schema):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str
    password_confirm: str


class LoginIn(Schema):
    email: str
    password: str


def user_payload(user: User):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role,
        "role_label": user.get_role_display(),
        "is_staff": user.is_staff,
    }


@router.post("/register", auth=None, response={201: dict, codes_4xx: ErrorOut})
@decorate_view(csrf_protect)
def register_user(request, payload: RegisterIn):
    email = payload.email.strip().lower()
    phone = payload.phone.strip()
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    if len(first_name) < 2 or len(last_name) < 2:
        return Status(400, {"detail": "نام و نام خانوادگی باید حداقل دو نویسه باشند."})
    try:
        validate_email(email)
    except ValidationError:
        return Status(400, {"detail": "فرمت ایمیل صحیح نیست."})
    if payload.password != payload.password_confirm:
        return Status(400, {"detail": "رمز عبور و تکرار آن یکسان نیستند."})
    if not phone.isdigit() or not 10 <= len(phone) <= 15:
        return Status(400, {"detail": "شماره موبایل معتبر نیست."})
    if User.objects.filter(email=email).exists():
        return Status(409, {"detail": "این ایمیل قبلاً ثبت شده است."})
    if User.objects.filter(phone=phone).exists():
        return Status(409, {"detail": "این شماره موبایل قبلاً ثبت شده است."})
    candidate = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=User.Role.STUDENT,
    )
    try:
        validate_password(payload.password, user=candidate)
    except ValidationError as exc:
        return Status(400, {"detail": " ".join(exc.messages)})
    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email,
                password=payload.password,
                first_name=candidate.first_name,
                last_name=candidate.last_name,
                phone=phone,
            )
    except IntegrityError:
        return Status(409, {"detail": "حسابی با این اطلاعات وجود دارد."})
    login(request, user)
    return Status(201, {"message": "حساب کاربری ساخته شد.", "user": user_payload(user)})


@router.post("/login", auth=None, response={200: dict, codes_4xx: ErrorOut})
@decorate_view(csrf_protect)
def login_user(request, payload: LoginIn):
    email = payload.email.strip().lower()
    existing_user = User.objects.filter(email=email).first()
    if existing_user and not existing_user.is_active and existing_user.check_password(payload.password):
        return Status(403, {"detail": "این حساب غیرفعال شده است."})
    user = authenticate(request, email=email, password=payload.password)
    if user is None:
        return Status(401, {"detail": "ایمیل یا رمز عبور نادرست است."})
    login(request, user)
    return {"message": "ورود موفق بود.", "user": user_payload(user)}


@router.post("/logout", auth=django_auth)
def logout_user(request):
    logout(request)
    return {"message": "از حساب کاربری خارج شدید."}


@router.get("/me", auth=django_auth)
def current_user(request):
    return user_payload(request.auth)
