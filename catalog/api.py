from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.responses import codes_4xx

from accounts.security import student_auth
from config.schemas import ErrorOut
from orders.models import Enrollment
from .models import Category, Course, Favorite, Review

router = Router(tags=["Catalog"])


class ReviewIn(Schema):
    rating: int
    comment: str


def serialize_course(course):
    return {
        "id": course.id,
        "code": course.code,
        "title": course.title,
        "slug": course.slug,
        "category": course.category.name,
        "instructor": course.instructor.full_name,
        "short_description": course.short_description,
        "price": course.price,
        "previous_price": course.previous_price,
        "duration_hours": float(course.duration_hours),
        "level": course.level,
        "level_label": course.get_level_display(),
        "image_url": course.image_url,
        "is_featured": course.is_featured,
        "is_bestseller": course.is_bestseller,
        "average_rating": float(getattr(course, "average_rating", 0) or 0),
        "reviews_count": getattr(course, "reviews_count", 0),
    }


@router.get("/categories", auth=None)
def list_categories(request):
    return list(Category.objects.filter(is_active=True).values("id", "name", "slug"))


@router.get("/courses", auth=None)
def list_courses(request, q: str = "", category: str = "", sort: str = "newest"):
    courses = Course.objects.filter(is_active=True).select_related("category", "instructor").annotate(
        average_rating=Avg("reviews__rating", filter=Q(reviews__status=Review.Status.APPROVED)),
        reviews_count=Count("reviews", filter=Q(reviews__status=Review.Status.APPROVED), distinct=True),
    )
    if q:
        courses = courses.filter(Q(title__icontains=q) | Q(short_description__icontains=q) | Q(code__icontains=q))
    if category:
        courses = courses.filter(category__slug=category)
    order_map = {"price_asc": "price", "price_desc": "-price", "title": "title", "newest": "-created_at"}
    courses = courses.order_by(order_map.get(sort, "-created_at"))
    return [serialize_course(course) for course in courses]


@router.get("/courses/{slug}", auth=None)
def course_detail(request, slug: str):
    course = get_object_or_404(
        Course.objects.select_related("category", "instructor")
        .prefetch_related("sections__lessons")
        .annotate(
            average_rating=Avg("reviews__rating", filter=Q(reviews__status=Review.Status.APPROVED)),
            reviews_count=Count(
                "reviews",
                filter=Q(reviews__status=Review.Status.APPROVED),
                distinct=True,
            ),
        ),
        slug=slug,
        is_active=True,
    )
    data = serialize_course(course)
    data["description"] = course.description
    data["sections"] = [
        {
            "title": section.title,
            "order": section.order,
            "lessons": [
                {"title": lesson.title, "duration_minutes": lesson.duration_minutes, "is_preview": lesson.is_preview}
                for lesson in section.lessons.all()
            ],
        }
        for section in course.sections.all()
    ]
    return data


@router.post("/courses/{course_id}/favorite", auth=student_auth)
def toggle_favorite(request, course_id: int):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    favorite, created = Favorite.objects.get_or_create(user=request.auth, course=course)
    if not created:
        favorite.delete()
    return {"is_favorite": created, "message": "به علاقه‌مندی‌ها افزوده شد." if created else "از علاقه‌مندی‌ها حذف شد."}


@router.post(
    "/courses/{course_id}/reviews",
    auth=student_auth,
    response={200: dict, 201: dict, codes_4xx: ErrorOut},
)
def create_review(request, course_id: int, payload: ReviewIn):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    if not 1 <= payload.rating <= 5:
        return Status(400, {"detail": "امتیاز باید بین ۱ تا ۵ باشد."})
    if len(payload.comment.strip()) < 5:
        return Status(400, {"detail": "متن نظر باید حداقل ۵ نویسه باشد."})
    if not Enrollment.objects.filter(user=request.auth, course=course, is_active=True).exists():
        return Status(403, {"detail": "فقط دانشجوی خریدار دوره می‌تواند نظر ثبت کند."})
    review, created = Review.objects.update_or_create(
        user=request.auth,
        course=course,
        defaults={"rating": payload.rating, "comment": payload.comment.strip(), "status": Review.Status.PENDING},
    )
    return Status(201 if created else 200, {"message": "نظر شما برای بررسی مدیر ثبت شد.", "review_id": review.id})
