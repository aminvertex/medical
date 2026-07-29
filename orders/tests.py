from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from accounts.models import User
from tests_support import json_request, make_course, make_paid_enrollment, make_user
from .models import CartItem, Coupon, CouponUsage, Enrollment, Order, Payment
from .services import StoreError, add_course, create_order, remove_course, simulate_payment, validate_coupon


class StoreWorkflowTests(TestCase):
    def setUp(self):
        self.student = make_user(email="buyer@example.com", phone="09120000201")
        self.other = make_user(email="other@example.com", phone="09120000202")
        self.admin = make_user(
            email="order-admin@example.com",
            phone="09120000203",
            role=User.Role.ADMIN,
        )
        self.course = make_course(code="ORD-101", slug="order-course", price=1_000_000)

    def create_pending_order(self, user=None, course=None, coupon_code=""):
        user = user or self.student
        course = course or self.course
        add_course(user, course.id)
        return create_order(
            user,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            coupon_code=coupon_code,
        )

    def test_add_remove_duplicate_missing_inactive_and_owned_course(self):
        add_course(self.student, self.course.id)
        with self.assertRaises(StoreError) as duplicate:
            add_course(self.student, self.course.id)
        self.assertEqual(duplicate.exception.status, 409)
        remove_course(self.student, self.course.id)
        with self.assertRaises(StoreError) as missing_remove:
            remove_course(self.student, self.course.id)
        self.assertEqual(missing_remove.exception.status, 404)

        self.course.is_active = False
        self.course.save(update_fields=["is_active"])
        with self.assertRaises(StoreError) as inactive:
            add_course(self.student, self.course.id)
        self.assertEqual(inactive.exception.status, 404)

        self.course.is_active = True
        self.course.save(update_fields=["is_active"])
        make_paid_enrollment(self.student, self.course)
        with self.assertRaises(StoreError) as purchased:
            add_course(self.student, self.course.id)
        self.assertEqual(purchased.exception.status, 409)

    def test_checkout_uses_server_price_snapshot_clears_cart_and_enrolls_after_payment(self):
        order = self.create_pending_order()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.items.get().unit_price, 1_000_000)
        self.assertEqual(order.payment.amount, 1_000_000)
        self.assertFalse(CartItem.objects.filter(cart__user=self.student).exists())

        self.course.price = 5_000_000
        self.course.save(update_fields=["price"])
        order.refresh_from_db()
        self.assertEqual(order.items.get().unit_price, 1_000_000)
        self.assertEqual(order.total_amount, 1_000_000)

        paid_order = simulate_payment(self.student, order.number)
        paid_order.refresh_from_db()
        self.assertEqual(paid_order.status, Order.Status.PAID)
        self.assertTrue(paid_order.payment.reference_code.startswith("SIM-"))
        self.assertTrue(Enrollment.objects.filter(user=self.student, course=self.course, is_active=True).exists())

    def test_empty_cart_and_inactive_course_at_checkout_are_rejected(self):
        with self.assertRaises(StoreError):
            create_order(
                self.student,
                first_name="علی",
                last_name="آزمایشی",
                email=self.student.email,
                phone=self.student.phone,
            )
        add_course(self.student, self.course.id)
        self.course.is_active = False
        self.course.save(update_fields=["is_active"])
        with self.assertRaises(StoreError) as ctx:
            create_order(
                self.student,
                first_name="علی",
                last_name="آزمایشی",
                email=self.student.email,
                phone=self.student.phone,
            )
        self.assertEqual(ctx.exception.status, 409)

    def test_payment_is_idempotent_and_repairs_missing_payment(self):
        order = self.create_pending_order()
        order.payment.delete()
        first = simulate_payment(self.student, order.number)
        second = simulate_payment(self.student, order.number)
        self.assertEqual(first.pk, second.pk)
        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.status, Payment.Status.SUCCESS)
        self.assertEqual(payment.amount, order.total_amount)
        self.assertEqual(Enrollment.objects.filter(user=self.student, course=self.course).count(), 1)

    def test_payment_repairs_wrong_payment_amount(self):
        order = self.create_pending_order()
        Payment.objects.filter(order=order).update(amount=1)
        simulate_payment(self.student, order.number)
        self.assertEqual(Payment.objects.get(order=order).amount, order.total_amount)

    def test_other_user_cannot_probe_or_pay_order_but_admin_can(self):
        order = self.create_pending_order()
        with self.assertRaises(StoreError) as other_error:
            simulate_payment(self.other, order.number)
        self.assertEqual(other_error.exception.status, 404)
        paid = simulate_payment(self.admin, order.number)
        self.assertEqual(paid.status, Order.Status.PAID)

    def test_cancelled_order_cannot_be_paid(self):
        order = self.create_pending_order()
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        with self.assertRaises(StoreError) as ctx:
            simulate_payment(self.student, order.number)
        self.assertEqual(ctx.exception.status, 409)

    def test_second_pending_order_for_same_course_cannot_be_paid_after_first(self):
        first = self.create_pending_order()
        second = self.create_pending_order()
        simulate_payment(self.student, first.number)
        with self.assertRaises(StoreError) as ctx:
            simulate_payment(self.student, second.number)
        self.assertEqual(ctx.exception.status, 409)
        second.refresh_from_db()
        self.assertEqual(second.status, Order.Status.PENDING)

    def test_inactive_enrollment_can_be_reactivated_by_new_purchase(self):
        old_order, _, enrollment = make_paid_enrollment(self.student, self.course)
        enrollment.is_active = False
        enrollment.save(update_fields=["is_active"])
        new_order = self.create_pending_order()
        simulate_payment(self.student, new_order.number)
        enrollment.refresh_from_db()
        self.assertTrue(enrollment.is_active)
        self.assertEqual(enrollment.order_item.order_id, new_order.id)
        self.assertNotEqual(enrollment.order_item.order_id, old_order.id)


class CouponTests(TestCase):
    def setUp(self):
        self.student = make_user(email="coupon@example.com", phone="09120000221")
        self.course = make_course(code="CPN-101", slug="coupon-course", price=1_000_000)
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SAVE20",
            title="تخفیف تست",
            discount_percent=20,
            min_order_amount=500_000,
            max_discount_amount=150_000,
            starts_at=now - timedelta(days=1),
            ends_at=now + timedelta(days=1),
            usage_limit=2,
            per_user_limit=1,
        )

    def create_order_with_coupon(self, user=None):
        user = user or self.student
        add_course(user, self.course.id)
        return create_order(
            user,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            coupon_code=self.coupon.code,
        )

    def test_coupon_normalizes_code_and_applies_max_discount(self):
        self.assertEqual(self.coupon.code, "SAVE20")
        order = self.create_order_with_coupon()
        self.assertEqual(order.subtotal, 1_000_000)
        self.assertEqual(order.discount_amount, 150_000)
        self.assertEqual(order.total_amount, 850_000)
        self.assertTrue(CouponUsage.objects.filter(order=order, coupon=self.coupon).exists())

    def test_invalid_expired_future_and_minimum_coupon_rejected(self):
        with self.assertRaises(StoreError):
            validate_coupon(self.student, "UNKNOWN", 1_000_000)
        self.coupon.ends_at = timezone.now() - timedelta(seconds=1)
        self.coupon.save(update_fields=["ends_at"])
        with self.assertRaises(StoreError):
            validate_coupon(self.student, self.coupon.code, 1_000_000)
        self.coupon.ends_at = timezone.now() + timedelta(days=2)
        self.coupon.starts_at = timezone.now() + timedelta(days=1)
        self.coupon.save(update_fields=["starts_at", "ends_at"])
        with self.assertRaises(StoreError):
            validate_coupon(self.student, self.coupon.code, 1_000_000)
        self.coupon.starts_at = timezone.now() - timedelta(days=1)
        self.coupon.save(update_fields=["starts_at"])
        with self.assertRaises(StoreError):
            validate_coupon(self.student, self.coupon.code, 100)

    def test_per_user_limit_is_enforced_at_payment(self):
        first = self.create_order_with_coupon()
        simulate_payment(self.student, first.number)
        second_course = make_course(
            code="CPN-202",
            slug="coupon-second-course",
            price=1_000_000,
            instructor=self.course.instructor,
        )
        add_course(self.student, second_course.id)
        with self.assertRaises(StoreError):
            create_order(
                self.student,
                first_name=self.student.first_name,
                last_name=self.student.last_name,
                email=self.student.email,
                phone=self.student.phone,
                coupon_code=self.coupon.code,
            )

    def test_global_usage_limit_is_enforced(self):
        users = [
            self.student,
            make_user(email="coupon2@example.com", phone="09120000222"),
            make_user(email="coupon3@example.com", phone="09120000223"),
        ]
        courses = [
            self.course,
            make_course(code="CPN-302", slug="coupon-302", instructor=self.course.instructor),
            make_course(code="CPN-303", slug="coupon-303", instructor=self.course.instructor),
        ]
        for user, course in zip(users[:2], courses[:2]):
            add_course(user, course.id)
            order = create_order(
                user,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=user.phone,
                coupon_code=self.coupon.code,
            )
            simulate_payment(user, order.number)
        add_course(users[2], courses[2].id)
        with self.assertRaises(StoreError):
            create_order(
                users[2],
                first_name=users[2].first_name,
                last_name=users[2].last_name,
                email=users[2].email,
                phone=users[2].phone,
                coupon_code=self.coupon.code,
            )


class StoreApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = make_user(email="api-buyer@example.com", phone="09120000241")
        self.other = make_user(email="api-other@example.com", phone="09120000242")
        self.course = make_course(code="API-ORD-101", slug="api-order-course")

    def test_anonymous_store_endpoints_are_protected(self):
        for method, path, payload in [
            ("get", "/api/v1/store/cart", None),
            ("post", "/api/v1/store/cart/items", {"course_id": self.course.id}),
            ("delete", f"/api/v1/store/cart/items/{self.course.id}", None),
            ("post", "/api/v1/store/checkout", {}),
            ("get", "/api/v1/store/orders", None),
        ]:
            with self.subTest(method=method, path=path):
                response = self.client.get(path) if method == "get" else json_request(self.client, method, path, payload)
                self.assertIn(response.status_code, (401, 403))

    def test_complete_api_cart_checkout_payment_and_order_list(self):
        self.client.force_login(self.student)
        added = json_request(self.client, "post", "/api/v1/store/cart/items", {"course_id": self.course.id})
        self.assertEqual(added.status_code, 201)
        self.assertEqual(added.json()["count"], 1)
        cart = self.client.get("/api/v1/store/cart")
        self.assertEqual(cart.status_code, 200)
        self.assertEqual(cart.json()["subtotal"], self.course.price)
        checkout = json_request(
            self.client,
            "post",
            "/api/v1/store/checkout",
            {
                "first_name": self.student.first_name,
                "last_name": self.student.last_name,
                "email": self.student.email,
                "phone": self.student.phone,
                "coupon_code": "",
            },
        )
        self.assertEqual(checkout.status_code, 201)
        order_number = checkout.json()["order_number"]
        payment = json_request(self.client, "post", f"/api/v1/store/orders/{order_number}/pay")
        self.assertEqual(payment.status_code, 200)
        self.assertEqual(payment.json()["status"], Order.Status.PAID)
        self.assertEqual(payment.json()["redirect_url"], f"/checkout/success/{order_number}/")
        orders = self.client.get("/api/v1/store/orders")
        self.assertEqual(orders.status_code, 200)
        self.assertEqual(orders.json()[0]["number"], order_number)

    def test_checkout_field_validation_and_empty_cart(self):
        self.client.force_login(self.student)
        base = {
            "first_name": "علی",
            "last_name": "دانشجو",
            "email": self.student.email,
            "phone": self.student.phone,
            "coupon_code": "",
        }
        cases = [
            ({"first_name": "ا"}, 400),
            ({"last_name": "ب"}, 400),
            ({"email": "bad"}, 400),
            ({"phone": "abc"}, 400),
        ]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                response = json_request(self.client, "post", "/api/v1/store/checkout", {**base, **changes})
                self.assertEqual(response.status_code, expected)
        empty = json_request(self.client, "post", "/api/v1/store/checkout", base)
        self.assertEqual(empty.status_code, 400)

    def test_delete_missing_cart_item_returns_404_json(self):
        self.client.force_login(self.student)
        response = json_request(self.client, "delete", f"/api/v1/store/cart/items/{self.course.id}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    def test_success_page_does_not_reveal_another_users_order(self):
        order, _, _ = make_paid_enrollment(self.student, self.course)
        self.client.force_login(self.other)
        response = self.client.get(f"/checkout/success/{order.number}/")
        self.assertEqual(response.status_code, 404)
