from django.db.models import Avg, Count, Q
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from accounts.models import InstructorProfile, User
from catalog.models import Course, Favorite, Review
from orders.models import Enrollment, Order


@ensure_csrf_cookie
def home(request):
    courses = Course.objects.filter(is_active=True).select_related("category", "instructor").annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__status=Review.Status.APPROVED)),
        sales_count=Count("order_items", filter=Q(order_items__order__status=Order.Status.PAID), distinct=True),
    ).order_by("-is_bestseller", "-sales_count", "-created_at")[:4]
    instructors = InstructorProfile.objects.filter(is_featured=True, user__is_active=True, user__role__in=[User.Role.INSTRUCTOR, User.Role.ADMIN]).select_related("user")[:4]
    stats = {
        "students": User.objects.filter(role=User.Role.STUDENT, is_active=True).count(),
        "courses": Course.objects.filter(is_active=True).count(),
        "enrollments": Enrollment.objects.filter(is_active=True).count(),
        "average_rating": Review.objects.filter(status=Review.Status.APPROVED).aggregate(avg=Avg("rating"))["avg"] or 0,
    }
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(
            Favorite.objects.filter(user=request.user).values_list("course_id", flat=True)
        )
    return render(
        request,
        "core/home.html",
        {
            "courses": courses,
            "instructors": instructors,
            "stats": stats,
            "favorite_ids": favorite_ids,
        },
    )


def about(request):
    return render(request, "core/about.html")


def team(request):
    instructors = InstructorProfile.objects.filter(user__is_active=True, user__role__in=[User.Role.INSTRUCTOR, User.Role.ADMIN]).select_related("user")
    return render(request, "core/team.html", {"instructors": instructors})


@ensure_csrf_cookie
def contact(request):
    return render(request, "core/contact.html")


def permission_denied_view(request, exception=None):
    return render(request, "errors/403.html", status=403)


def page_not_found_view(request, exception=None):
    return render(request, "errors/404.html", status=404)
