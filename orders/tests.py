from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Course
from .models import CartItem, Enrollment, Order
from .services import StoreError, add_course, create_order, simulate_payment


class StoreWorkflowTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            first_name="علی",
            last_name="دانشجو",
            phone="09120000011",
        )
        self.instructor = User.objects.create_user(
            email="teacher@example.com",
            password="StrongPass123!",
            first_name="مدرس",
            last_name="نمونه",
            phone="09120000012",
            role=User.Role.INSTRUCTOR,
        )
        category = Category.objects.create(name="یادگیری ماشین", slug="ml")
        self.course = Course.objects.create(
            code="ML-101",
            title="یادگیری ماشین",
            slug="machine-learning",
            category=category,
            instructor=self.instructor,
            short_description="دوره آزمایشی",
            description="توضیحات دوره آزمایشی",
            price=1_000_000,
            duration_hours=10,
        )

    def test_duplicate_course_cannot_be_added_to_cart(self):
        add_course(self.student, self.course.id)
        with self.assertRaises(StoreError) as ctx:
            add_course(self.student, self.course.id)
        self.assertEqual(ctx.exception.status, 409)
        self.assertEqual(CartItem.objects.filter(cart__user=self.student).count(), 1)

    def test_checkout_uses_server_price_snapshot_then_enrolls_after_payment(self):
        add_course(self.student, self.course.id)
        order = create_order(
            self.student,
            first_name="علی",
            last_name="دانشجو",
            email=self.student.email,
            phone=self.student.phone,
        )
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.items.get().unit_price, 1_000_000)
        self.assertEqual(order.payment.amount, 1_000_000)
        self.assertFalse(CartItem.objects.filter(cart__user=self.student).exists())

        self.course.price = 5_000_000
        self.course.save(update_fields=["price"])
        order.refresh_from_db()
        self.assertEqual(order.items.get().unit_price, 1_000_000)

        paid_order = simulate_payment(self.student, order.number)
        self.assertEqual(paid_order.status, Order.Status.PAID)
        self.assertTrue(paid_order.payment.reference_code.startswith("SIM-"))
        self.assertTrue(Enrollment.objects.filter(user=self.student, course=self.course, is_active=True).exists())

    def test_user_cannot_buy_an_enrolled_course_again(self):
        add_course(self.student, self.course.id)
        order = create_order(
            self.student,
            first_name="علی",
            last_name="دانشجو",
            email=self.student.email,
            phone=self.student.phone,
        )
        simulate_payment(self.student, order.number)
        with self.assertRaises(StoreError) as ctx:
            add_course(self.student, self.course.id)
        self.assertEqual(ctx.exception.status, 409)
