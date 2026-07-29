from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.responses import codes_4xx

from accounts.models import InstructorProfile, User
from accounts.security import admin_auth
from config.schemas import ErrorOut
from catalog.models import Course, Review
from core.models import ContactMessage
from orders.models import Enrollment, Order

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
    if q:
        from django.db.models import Q
        users = users.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q))
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
            "role_label": user.get_role_display(),
            "is_active": user.is_active,
            "date_joined": user.date_joined.isoformat(),
        }
        for user in users[:200]
    ]


@router.patch("/users/{user_id}", auth=admin_auth, response={200: dict, codes_4xx: ErrorOut})
def update_user(request, user_id: int, payload: UserUpdateIn):
    user = get_object_or_404(User, id=user_id)
    if user.id == request.auth.id and payload.is_active is False:
        return Status(400, {"detail": "مدیر نمی‌تواند حساب خودش را غیرفعال کند."})
    if payload.role is not None:
        allowed = {choice for choice, _ in User.Role.choices}
        if payload.role not in allowed:
            return Status(400, {"detail": "نقش نامعتبر است."})
        if user.is_superuser and payload.role != User.Role.ADMIN:
            return Status(400, {"detail": "نقش مدیر ارشد از این مسیر تغییر نمی‌کند."})
        if payload.role == User.Role.STUDENT and user.taught_courses.exists():
            return Status(409, {"detail": "ابتدا دوره‌های این مدرس را به مدرس دیگری منتقل کنید."})
        user.role = payload.role
        user.is_staff = payload.role == User.Role.ADMIN or user.is_superuser
        if payload.role == User.Role.INSTRUCTOR:
            InstructorProfile.objects.get_or_create(
                user=user,
                defaults={"title": "مدرس آکادمی", "bio": "پروفایل مدرس را تکمیل کنید.", "expertise": "هوش مصنوعی"},
            )
    if payload.is_active is not None:
        user.is_active = payload.is_active
    user.save()
    return {"message": "اطلاعات کاربر به‌روزرسانی شد."}


@router.patch("/courses/{course_id}/status", auth=admin_auth)
def update_course_status(request, course_id: int, payload: CourseStatusIn):
    course = get_object_or_404(Course, id=course_id)
    course.is_active = payload.is_active
    course.save(update_fields=["is_active", "updated_at"])
    return {"message": "وضعیت دوره تغییر کرد.", "is_active": course.is_active}


@router.patch("/messages/{message_id}", auth=admin_auth, response={200: dict, codes_4xx: ErrorOut})
def update_message_status(request, message_id: int, payload: MessageStatusIn):
    message = get_object_or_404(ContactMessage, id=message_id)
    allowed = {choice for choice, _ in ContactMessage.Status.choices}
    if payload.status not in allowed:
        return Status(400, {"detail": "وضعیت نامعتبر است."})
    message.status = payload.status
    message.save(update_fields=["status"])
    return {"message": "وضعیت پیام به‌روزرسانی شد."}
