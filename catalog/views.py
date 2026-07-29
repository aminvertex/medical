from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Course, Favorite, Review


def shop(request):
    q = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "newest")
    courses = Course.objects.filter(is_active=True).select_related("category", "instructor").annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__status=Review.Status.APPROVED)),
        sales_count=Count("order_items", filter=Q(order_items__order__status="PAID"), distinct=True),
    )
    if q:
        courses = courses.filter(Q(title__icontains=q) | Q(short_description__icontains=q) | Q(code__icontains=q))
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    order_map = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "title": "title",
        "bestseller": "-sales_count",
    }
    courses = courses.order_by(order_map.get(sort, "-created_at"))
    favorite_ids = set()
    if request.user.is_authenticated:
        favorite_ids = set(Favorite.objects.filter(user=request.user).values_list("course_id", flat=True))
    context = {
        "courses": courses,
        "categories": Category.objects.filter(is_active=True),
        "q": q,
        "selected_category": category_slug,
        "selected_sort": sort,
        "favorite_ids": favorite_ids,
    }
    return render(request, "catalog/shop.html", context)


def course_detail(request, slug):
    course = get_object_or_404(
        Course.objects.filter(is_active=True)
        .select_related("category", "instructor")
        .prefetch_related("sections__lessons", "reviews__user"),
        slug=slug,
    )
    approved_reviews = course.reviews.filter(status=Review.Status.APPROVED).select_related("user")
    rating = approved_reviews.aggregate(avg=Avg("rating"))["avg"] or 0
    related = Course.objects.filter(is_active=True, category=course.category).exclude(pk=course.pk).select_related("category", "instructor")[:3]
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, course=course).exists()
    context = {
        "course": course,
        "approved_reviews": approved_reviews,
        "rating": rating,
        "rating_count": approved_reviews.count(),
        "related_courses": related,
        "is_favorite": is_favorite,
    }
    return render(request, "catalog/course_detail.html", context)
