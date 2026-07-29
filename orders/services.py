import secrets
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from catalog.models import Course
from .models import Cart, CartItem, Coupon, CouponUsage, Enrollment, Order, OrderItem, Payment


class StoreError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


@dataclass
class PriceSummary:
    subtotal: int
    discount: int
    total: int
    coupon: Coupon | None


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def add_course(user, course_id: int):
    course = Course.objects.filter(pk=course_id, is_active=True).first()
    if not course:
        raise StoreError("دوره پیدا نشد.", 404)
    if Enrollment.objects.filter(user=user, course=course, is_active=True).exists():
        raise StoreError("این دوره قبلاً خریداری شده است.", 409)
    cart = get_cart(user)
    item, created = CartItem.objects.get_or_create(cart=cart, course=course)
    if not created:
        raise StoreError("این دوره از قبل در سبد خرید است.", 409)
    return item


def remove_course(user, course_id: int):
    cart = get_cart(user)
    deleted, _ = CartItem.objects.filter(cart=cart, course_id=course_id).delete()
    if not deleted:
        raise StoreError("این دوره در سبد خرید وجود ندارد.", 404)


def validate_coupon(user, code: str, subtotal: int):
    if not code:
        return None
    now = timezone.now()
    coupon = Coupon.objects.filter(code=code.strip().upper(), is_active=True).first()
    if not coupon:
        raise StoreError("کد تخفیف معتبر نیست.")
    if coupon.starts_at > now or coupon.ends_at < now:
        raise StoreError("زمان استفاده از این کد تخفیف گذشته یا هنوز شروع نشده است.")
    if subtotal < coupon.min_order_amount:
        raise StoreError("مبلغ سفارش برای استفاده از این کد کافی نیست.")
    paid_usages = coupon.usages.filter(order__status=Order.Status.PAID)
    if coupon.usage_limit is not None and paid_usages.count() >= coupon.usage_limit:
        raise StoreError("ظرفیت استفاده از این کد تکمیل شده است.")
    if paid_usages.filter(user=user).count() >= coupon.per_user_limit:
        raise StoreError("شما قبلاً از این کد استفاده کرده‌اید.")
    return coupon


def calculate_prices(user, items, coupon_code=""):
    subtotal = sum(item.course.price for item in items)
    coupon = validate_coupon(user, coupon_code, subtotal) if coupon_code else None
    discount = 0
    if coupon:
        discount = subtotal * coupon.discount_percent // 100
        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
    return PriceSummary(subtotal=subtotal, discount=discount, total=max(subtotal - discount, 0), coupon=coupon)


@transaction.atomic
def create_order(user, *, first_name, last_name, email, phone, coupon_code=""):
    cart = Cart.objects.select_for_update().filter(user=user).first()
    if not cart:
        raise StoreError("سبد خرید خالی است.")
    items = list(CartItem.objects.select_for_update().filter(cart=cart).select_related("course"))
    if not items:
        raise StoreError("سبد خرید خالی است.")
    purchased_ids = set(Enrollment.objects.filter(user=user, is_active=True).values_list("course_id", flat=True))
    duplicate = next((item.course.title for item in items if item.course_id in purchased_ids), None)
    if duplicate:
        raise StoreError(f"دوره «{duplicate}» قبلاً خریداری شده است.", 409)
    inactive = next((item.course.title for item in items if not item.course.is_active), None)
    if inactive:
        raise StoreError(f"دوره «{inactive}» دیگر قابل خرید نیست.", 409)
    prices = calculate_prices(user, items, coupon_code)
    order = Order.objects.create(
        user=user,
        coupon=prices.coupon,
        subtotal=prices.subtotal,
        discount_amount=prices.discount,
        total_amount=prices.total,
        customer_first_name=first_name.strip(),
        customer_last_name=last_name.strip(),
        customer_email=email.strip().lower(),
        customer_phone=phone.strip(),
    )
    for item in items:
        OrderItem.objects.create(
            order=order,
            course=item.course,
            course_code=item.course.code,
            course_title=item.course.title,
            unit_price=item.course.price,
        )
    Payment.objects.create(order=order, amount=prices.total)
    if prices.coupon:
        CouponUsage.objects.create(coupon=prices.coupon, user=user, order=order)
    CartItem.objects.filter(cart=cart).delete()
    return order


@transaction.atomic
def simulate_payment(user, order_number: str):
    order = Order.objects.select_for_update().select_related("payment", "coupon").prefetch_related("items__course").filter(number=order_number).first()
    if not order:
        raise StoreError("سفارش پیدا نشد.", 404)
    if order.user_id != user.id and not user.is_admin_role:
        raise StoreError("این سفارش متعلق به شما نیست.", 403)
    if order.status == Order.Status.PAID:
        return order
    if order.status != Order.Status.PENDING:
        raise StoreError("این سفارش قابل پرداخت نیست.", 409)
    if order.coupon_id:
        # اعتبار تخفیف در لحظه پرداخت دوباره کنترل می‌شود تا سفارش‌های معطل
        # نتوانند ظرفیت یا محدودیت هر کاربر را دور بزنند.
        validate_coupon(order.user, order.coupon.code, order.subtotal)
    now = timezone.now()
    order.status = Order.Status.PAID
    order.paid_at = now
    order.save(update_fields=["status", "paid_at", "updated_at"])
    payment = order.payment
    payment.status = Payment.Status.SUCCESS
    payment.reference_code = f"SIM-{timezone.localdate():%Y%m%d}-{secrets.token_hex(4).upper()}"
    payment.paid_at = now
    payment.save(update_fields=["status", "reference_code", "paid_at"])
    for item in order.items.all():
        if item.course_id:
            enrollment, created = Enrollment.objects.get_or_create(
                user=order.user,
                course=item.course,
                defaults={"order_item": item, "is_active": True},
            )
            if not created and not enrollment.is_active:
                enrollment.is_active = True
                enrollment.order_item = item
                enrollment.save(update_fields=["is_active", "order_item"])
    return order
