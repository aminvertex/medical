from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from orders.models import Enrollment
from tests_support import json_request, make_course, make_paid_enrollment, make_user
from .models import Category, Course, Favorite, Review


class CatalogPublicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = make_course(code="CAT-101", slug="catalog-course", price=900_000)
        self.other = make_course(code="CAT-202", slug="second-course", price=1_500_000, instructor=self.course.instructor)
        self.other.category = Category.objects.create(name="دسته دوم", slug="second-category")
        self.other.save(update_fields=["category"])

    def test_public_catalog_pages_and_apis_render(self):
        cases = [
            (reverse("shop"), 200),
            (reverse("course_detail", kwargs={"slug": self.course.slug}), 200),
            ("/api/v1/catalog/categories", 200),
            ("/api/v1/catalog/courses", 200),
            (f"/api/v1/catalog/courses/{self.course.slug}", 200),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, expected)

    def test_inactive_courses_are_not_public(self):
        self.course.is_active = False
        self.course.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(reverse("course_detail", kwargs={"slug": self.course.slug})).status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/catalog/courses/{self.course.slug}").status_code, 404)
        ids = {item["id"] for item in self.client.get("/api/v1/catalog/courses").json()}
        self.assertNotIn(self.course.id, ids)

    def test_search_category_and_sort_filters(self):
        search = self.client.get("/api/v1/catalog/courses", {"q": "CAT-101"}).json()
        self.assertEqual([item["id"] for item in search], [self.course.id])
        category = self.client.get("/api/v1/catalog/courses", {"category": "second-category"}).json()
        self.assertEqual([item["id"] for item in category], [self.other.id])
        ascending = self.client.get("/api/v1/catalog/courses", {"sort": "price_asc"}).json()
        self.assertEqual([item["id"] for item in ascending], [self.course.id, self.other.id])
        descending = self.client.get("/api/v1/catalog/courses", {"sort": "price_desc"}).json()
        self.assertEqual([item["id"] for item in descending], [self.other.id, self.course.id])

    def test_unknown_sort_falls_back_without_error(self):
        response = self.client.get("/api/v1/catalog/courses", {"sort": "invalid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)


class FavoriteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user(email="favorite@example.com", phone="09120000101")
        self.course = make_course(code="FAV-101", slug="favorite-course")

    def test_anonymous_cannot_toggle_favorite(self):
        response = json_request(self.client, "post", f"/api/v1/catalog/courses/{self.course.id}/favorite")
        self.assertIn(response.status_code, (401, 403))

    def test_toggle_favorite_is_reversible_and_unique(self):
        self.client.force_login(self.user)
        first = json_request(self.client, "post", f"/api/v1/catalog/courses/{self.course.id}/favorite")
        second = json_request(self.client, "post", f"/api/v1/catalog/courses/{self.course.id}/favorite")
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()["is_favorite"])
        self.assertFalse(second.json()["is_favorite"])
        self.assertFalse(Favorite.objects.filter(user=self.user, course=self.course).exists())

    def test_inactive_or_missing_course_cannot_be_favorited(self):
        self.client.force_login(self.user)
        self.course.is_active = False
        self.course.save(update_fields=["is_active"])
        self.assertEqual(json_request(self.client, "post", f"/api/v1/catalog/courses/{self.course.id}/favorite").status_code, 404)
        self.assertEqual(json_request(self.client, "post", "/api/v1/catalog/courses/999999/favorite").status_code, 404)


class ReviewPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = make_user(email="reviewer@example.com", phone="09120000111")
        self.course = make_course(code="REV-101", slug="review-course", price=900_000)
        self.client.force_login(self.student)

    def test_non_buyer_cannot_review(self):
        response = json_request(
            self.client,
            "post",
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            {"rating": 5, "comment": "دوره خوبی است"},
        )
        self.assertEqual(response.status_code, 403)

    def test_rating_and_comment_validation(self):
        make_paid_enrollment(self.student, self.course)
        cases = [
            ({"rating": 0, "comment": "نظر معتبر است"}, 400),
            ({"rating": 6, "comment": "نظر معتبر است"}, 400),
            ({"rating": 5, "comment": "کم"}, 400),
            ({"rating": 5, "comment": "x" * 3001}, 400),
        ]
        for payload, expected in cases:
            with self.subTest(payload={"rating": payload["rating"], "length": len(payload["comment"])}):
                response = json_request(
                    self.client,
                    "post",
                    f"/api/v1/catalog/courses/{self.course.id}/reviews",
                    payload,
                )
                self.assertEqual(response.status_code, expected)

    def test_buyer_review_is_pending_and_update_does_not_duplicate(self):
        make_paid_enrollment(self.student, self.course)
        first = json_request(
            self.client,
            "post",
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            {"rating": 5, "comment": "محتوای پروژه‌محور و مفید بود."},
        )
        second = json_request(
            self.client,
            "post",
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            {"rating": 4, "comment": "نسخه ویرایش‌شده نظر من است."},
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Review.objects.filter(user=self.student, course=self.course).count(), 1)
        review = Review.objects.get(user=self.student, course=self.course)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.status, Review.Status.PENDING)

    def test_inactive_enrollment_does_not_allow_review(self):
        _, _, enrollment = make_paid_enrollment(self.student, self.course)
        enrollment.is_active = False
        enrollment.save(update_fields=["is_active"])
        response = json_request(
            self.client,
            "post",
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            {"rating": 5, "comment": "نظر معتبر اما بدون دسترسی فعال"},
        )
        self.assertEqual(response.status_code, 403)

    def test_only_approved_reviews_appear_on_public_detail(self):
        make_paid_enrollment(self.student, self.course)
        Review.objects.create(user=self.student, course=self.course, rating=5, comment="نظر پنهان", status=Review.Status.PENDING)
        response = self.client.get(reverse("course_detail", kwargs={"slug": self.course.slug}))
        self.assertNotContains(response, "نظر پنهان")
        Review.objects.filter(user=self.student, course=self.course).update(status=Review.Status.APPROVED)
        response = self.client.get(reverse("course_detail", kwargs={"slug": self.course.slug}))
        self.assertContains(response, "نظر پنهان")
