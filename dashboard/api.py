from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.responses import codes_4xx

from accounts.models import InstructorProfile, User
from accounts.security import admin_auth
from catalog.models import Course, Review
from config.schemas import ErrorOut
from core.models import ContactMessage
from orders.models import Order

router = Router(tags=["Admin Dashboard"])


class UserUpdateIn(Schema):
    role: str | None = None
    is_active: bool | None = None


class CourseStatusIn(Schema):
    is_active: bool


class MessageStatusIn(Schema):
    status: str


@router.get("/stats", auth=admin_auth)
def admin_stats(request):
    paid = Order.objects.filter(status=Order.Status.PAID)
    return {
        "users": User.objects.count(),
        "students": User.objects.filter(role=User.Role.STUDENT).count(),
        "instructors": User.objects.filter(role=User.Role.INSTRUCTOR).count(),
        "active_courses": Course.objects.filter(is_active=True).count(),
        "paid_orders": paid.count(),
        "revenue": paid.aggregate(total=Sum("total_amount"))["total"] or 0,
        "pending_reviews": Review.objects.filter(status=Review.Status.PENDING).count(),
        "new_messages": ContactMessage.objects.filter(status=ContactMessage.Status.NEW).count(),
    }


@router.get("/users", auth=admin_auth)
def list_users(request, q: str = ""):
    users = User.objects.all()
    q = q.strip()
    if q:
        users = users.filter(
            Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
        )
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
            "role_label": user.get_role_display(),
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "date_joined": user.date_joined.isoformat(),
        }
        for user in users[:200]
    ]


@router.patch(
    "/users/{user_id}",
    auth=admin_auth,
    response={200: dict, codes_4xx: ErrorOut},
)
@transaction.atomic
def update_user(request, user_id: int, payload: UserUpdateIn):
    user = get_object_or_404(User.objects.select_for_update(), id=user_id)
    if payload.role is None and payload.is_active is None:
        return Status(400, {"detail": "حداقل یک مقدار برای تغییر ارسال کنید."})

    is_self = user.id == request.auth.id
    if user.is_superuser:
        if payload.role not in (None, User.Role.ADMIN) or payload.is_active is False:
            return Status(400, {"detail": "مدیر ارشد از پنل سفارشی تغییر یا غیرفعال نمی‌شود."})
    if is_self and payload.is_active is False:
        return Status(400, {"detail": "مدیر نمی‌تواند حساب خودش را غیرفعال کند."})
    if is_self and payload.role is not None and payload.role != User.Role.ADMIN:
        return Status(400, {"detail": "مدیر نمی‌تواند نقش خودش را کاهش دهد."})
    if payload.is_active is False and user.taught_courses.filter(is_active=True).exists():
        return Status(
            409,
            {"detail": "ابتدا دوره‌های فعال این مدرس را متوقف یا به مدرس دیگری منتقل کنید."},
        )

    if payload.role is not None:
        allowed = {choice for choice, _ in User.Role.choices}
        if payload.role not in allowed:
            return Status(400, {"detail": "نقش نامعتبر است."})
        if payload.role == User.Role.STUDENT and user.taught_courses.exists():
            return Status(
                409,
                {"detail": "ابتدا دوره‌های این مدرس را به مدرس دیگری منتقل کنید."},
            )
        user.role = payload.role
        if payload.role == User.Role.INSTRUCTOR:
            InstructorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "title": "مدرس آکادمی",
                    "bio": "پروفایل مدرس را تکمیل کنید.",
                    "expertise": "هوش مصنوعی",
                },
            )
    if payload.is_active is not None:
        user.is_active = payload.is_active
    user.save()
    return {
        "message": "اطلاعات کاربر به‌روزرسانی شد.",
        "user": {
            "id": user.id,
            "role": user.role,
            "role_label": user.get_role_display(),
            "is_active": user.is_active,
        },
    }


@router.patch("/courses/{course_id}/status", auth=admin_auth)
def update_course_status(request, course_id: int, payload: CourseStatusIn):
    course = get_object_or_404(Course, id=course_id)
    course.is_active = payload.is_active
    course.save(update_fields=["is_active", "updated_at"])
    return {"message": "وضعیت دوره تغییر کرد.", "is_active": course.is_active}


@router.patch(
    "/messages/{message_id}",
    auth=admin_auth,
    response={200: dict, codes_4xx: ErrorOut},
)
def update_message_status(request, message_id: int, payload: MessageStatusIn):
    message = get_object_or_404(ContactMessage, id=message_id)
    allowed = {choice for choice, _ in ContactMessage.Status.choices}
    if payload.status not in allowed:
        return Status(400, {"detail": "وضعیت نامعتبر است."})
    message.status = payload.status
    message.save(update_fields=["status"])
    return {"message": "وضعیت پیام به‌روزرسانی شد."}
