import json
import zlib

from django.test import Client

from accounts.models import User
from catalog.models import Category, Course
from orders.models import Enrollment, Order, OrderItem, Payment

DEFAULT_PASSWORD = "StrongPass123!"


def make_user(*, email, phone, role=User.Role.STUDENT, password=DEFAULT_PASSWORD, **extra):
    defaults = {
        "first_name": extra.pop("first_name", "کاربر"),
        "last_name": extra.pop("last_name", "آزمایشی"),
        "phone": phone,
        "role": role,
        **extra,
    }
    return User.objects.create_user(email=email, password=password, **defaults)


def make_course(*, code="AI-TEST-101", slug="ai-test", price=1_000_000, active=True, instructor=None):
    if instructor is None:
        instructor = make_user(
            email=f"teacher-{code.lower()}@example.com",
            phone=f"09{zlib.crc32(code.encode('utf-8')) % 10**9:09d}",
            role=User.Role.INSTRUCTOR,
            first_name="مدرس",
            last_name="آزمایشی",
        )
    category, _ = Category.objects.get_or_create(
        slug="test-category",
        defaults={"name": "دسته آزمایشی", "is_active": True},
    )
    return Course.objects.create(
        code=code,
        title=f"دوره {code}",
        slug=slug,
        category=category,
        instructor=instructor,
        short_description="توضیح کوتاه معتبر برای دوره آزمایشی",
        description="توضیحات کامل دوره آزمایشی",
        price=price,
        is_active=active,
    )


def make_paid_enrollment(user, course, *, number=None, price=None):
    amount = course.price if price is None else price
    order = Order.objects.create(
        number=number or "",
        user=user,
        status=Order.Status.PAID,
        subtotal=amount,
        discount_amount=0,
        total_amount=amount,
        customer_first_name=user.first_name,
        customer_last_name=user.last_name,
        customer_email=user.email,
        customer_phone=user.phone or "09120000000",
    )
    item = OrderItem.objects.create(
        order=order,
        course=course,
        course_code=course.code,
        course_title=course.title,
        unit_price=amount,
    )
    Payment.objects.create(
        order=order,
        amount=amount,
        status=Payment.Status.SUCCESS,
        reference_code=f"SIM-TEST-{order.pk}",
    )
    enrollment = Enrollment.objects.create(user=user, course=course, order_item=item)
    return order, item, enrollment


def json_request(client: Client, method: str, path: str, payload=None, *, csrf_token=None):
    kwargs = {
        "data": json.dumps(payload if payload is not None else {}),
        "content_type": "application/json",
    }
    if csrf_token:
        kwargs["HTTP_X_CSRFTOKEN"] = csrf_token
    return getattr(client, method.lower())(path, **kwargs)


def csrf_token(client: Client, path="/"):
    response = client.get(path)
    assert response.status_code < 500, response.status_code
    return client.cookies["csrftoken"].value
