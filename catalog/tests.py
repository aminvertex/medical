import json

from django.test import Client, TestCase

from accounts.models import User
from orders.models import Enrollment, Order, OrderItem
from .models import Category, Course, Review


class ReviewPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            first_name="کاربر",
            last_name="نمونه",
            phone="09120000021",
        )
        teacher = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123!",
            first_name="مدرس",
            last_name="نمونه",
            phone="09120000022",
            role=User.Role.INSTRUCTOR,
        )
        category = Category.objects.create(name="علم داده", slug="data")
        self.course = Course.objects.create(
            code="DATA-101",
            title="علم داده",
            slug="data-science",
            category=category,
            instructor=teacher,
            short_description="توضیح کوتاه",
            description="توضیحات کامل",
            price=900_000,
        )
        self.client.force_login(self.student)

    def test_non_buyer_cannot_review(self):
        response = self.client.post(
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            data=json.dumps({"rating": 5, "comment": "دوره خوبی است"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_buyer_review_is_pending_for_admin_approval(self):
        order = Order.objects.create(
            user=self.student,
            status=Order.Status.PAID,
            subtotal=900_000,
            total_amount=900_000,
            customer_first_name=self.student.first_name,
            customer_last_name=self.student.last_name,
            customer_email=self.student.email,
            customer_phone=self.student.phone,
        )
        item = OrderItem.objects.create(
            order=order,
            course=self.course,
            course_code=self.course.code,
            course_title=self.course.title,
            unit_price=self.course.price,
        )
        Enrollment.objects.create(user=self.student, course=self.course, order_item=item)
        response = self.client.post(
            f"/api/v1/catalog/courses/{self.course.id}/reviews",
            data=json.dumps({"rating": 5, "comment": "محتوای پروژه‌محور و مفید بود."}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.get().status, Review.Status.PENDING)
