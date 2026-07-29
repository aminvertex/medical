from django.db.models import BigIntegerField, Count, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render

from accounts.models import User
from accounts.security import role_required
from catalog.models import Course, Review
from core.models import ContactMessage
from orders.models import Enrollment, Order, OrderItem


@role_required(User.Role.ADMIN)
def dashboard_home(request):
    paid_orders = Order.objects.filter(status=Order.Status.PAID)
    context = {
        "users_count": User.objects.count(),
        "courses_count": Course.objects.filter(is_active=True).count(),
        "orders_count": paid_orders.count(),
        "revenue": paid_orders.aggregate(total=Sum("total_amount"))["total"] or 0,
        "pending_reviews": Review.objects.filter(status=Review.Status.PENDING).count(),
        "new_messages": ContactMessage.objects.filter(status=ContactMessage.Status.NEW).count(),
        "recent_orders": Order.objects.select_related("user").prefetch_related("items")[:8],
        "top_courses": Course.objects.annotate(sales=Count("order_items", filter=Q(order_items__order__status=Order.Status.PAID))).order_by("-sales")[:5],
    }
    return render(request, "dashboard/index.html", context)


@role_required(User.Role.ADMIN)
def dashboard_users(request):
    users = User.objects.all()[:200]
    return render(request, "dashboard/users.html", {"users": users, "roles": User.Role.choices})


@role_required(User.Role.ADMIN)
def dashboard_courses(request):
    courses = Course.objects.select_related("category", "instructor").annotate(
        enrollments_count=Count("enrollments", distinct=True)
    )
    return render(request, "dashboard/courses.html", {"courses": courses})


@role_required(User.Role.ADMIN)
def dashboard_orders(request):
    orders = Order.objects.select_related("user", "payment").prefetch_related("items")[:300]
    return render(request, "dashboard/orders.html", {"orders": orders})


@role_required(User.Role.ADMIN)
def dashboard_messages(request):
    messages = ContactMessage.objects.all()[:300]
    return render(request, "dashboard/messages.html", {"contact_messages": messages, "statuses": ContactMessage.Status.choices})


@role_required(User.Role.INSTRUCTOR, User.Role.ADMIN)
def instructor_dashboard(request):
    paid_revenue = (
        OrderItem.objects.filter(
            course_id=OuterRef("pk"),
            order__status=Order.Status.PAID,
        )
        .values("course_id")
        .annotate(total=Sum("unit_price"))
        .values("total")[:1]
    )
    courses = Course.objects.filter(instructor=request.user).annotate(
        students_count=Count(
            "enrollments",
            filter=Q(enrollments__is_active=True),
            distinct=True,
        ),
        revenue=Coalesce(
            Subquery(paid_revenue, output_field=BigIntegerField()),
            Value(0, output_field=BigIntegerField()),
            output_field=BigIntegerField(),
        ),
    )
    course_ids = list(courses.values_list("id", flat=True))
    context = {
        "courses": courses,
        "students_count": Enrollment.objects.filter(course_id__in=course_ids, is_active=True).values("user_id").distinct().count(),
        "sales_count": Order.objects.filter(status=Order.Status.PAID, items__course_id__in=course_ids).distinct().count(),
    }
    return render(request, "instructor/dashboard.html", context)
