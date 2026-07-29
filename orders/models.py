import secrets
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from catalog.models import Course


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart", verbose_name="کاربر")
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("ویرایش", auto_now=True)

    class Meta:
        verbose_name = "سبد خرید"
        verbose_name_plural = "سبدهای خرید"

    def __str__(self):
        return f"سبد {self.user.email}"

    @property
    def subtotal(self):
        return sum(item.course.price for item in self.items.select_related("course").all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items", verbose_name="سبد")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="cart_items", verbose_name="دوره")
    added_at = models.DateTimeField("افزوده‌شده", auto_now_add=True)

    class Meta:
        verbose_name = "ردیف سبد"
        verbose_name_plural = "ردیف‌های سبد"
        ordering = ["added_at"]
        constraints = [
            models.UniqueConstraint(fields=["cart", "course"], name="uniq_cart_course")
        ]

    def __str__(self):
        return f"{self.cart.user.email}: {self.course.title}"


class Coupon(models.Model):
    code = models.CharField("کد", max_length=30, unique=True)
    title = models.CharField("عنوان", max_length=120)
    discount_percent = models.PositiveSmallIntegerField(
        "درصد تخفیف", validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    min_order_amount = models.PositiveBigIntegerField("حداقل مبلغ سفارش", default=0)
    max_discount_amount = models.PositiveBigIntegerField("سقف تخفیف", null=True, blank=True)
    starts_at = models.DateTimeField("شروع")
    ends_at = models.DateTimeField("پایان")
    usage_limit = models.PositiveIntegerField("سقف استفاده کل", null=True, blank=True)
    per_user_limit = models.PositiveSmallIntegerField("سقف استفاده هر کاربر", default=1)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار پرداخت"
        PAID = "PAID", "پرداخت‌شده"
        CANCELLED = "CANCELLED", "لغوشده"
        REFUNDED = "REFUNDED", "بازگشت وجه"

    number = models.CharField("شماره سفارش", max_length=32, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders", verbose_name="مشتری")
    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders", verbose_name="کد تخفیف")
    subtotal = models.PositiveBigIntegerField("جمع اولیه")
    discount_amount = models.PositiveBigIntegerField("مبلغ تخفیف", default=0)
    total_amount = models.PositiveBigIntegerField("مبلغ نهایی")
    customer_first_name = models.CharField("نام خریدار", max_length=80)
    customer_last_name = models.CharField("نام خانوادگی خریدار", max_length=100)
    customer_email = models.EmailField("ایمیل خریدار")
    customer_phone = models.CharField("موبایل خریدار", max_length=15)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)
    paid_at = models.DateTimeField("پرداخت", null=True, blank=True)
    updated_at = models.DateTimeField("ویرایش", auto_now=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"], name="order_status_date_idx"),
            models.Index(fields=["user", "status"], name="order_user_status_idx"),
        ]
        permissions = [
            ("view_sales_dashboard", "Can view sales dashboard"),
            ("refund_order", "Can refund paid order"),
        ]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = f"MAH-{timezone.localdate():%y%m%d}-{secrets.token_hex(5).upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="سفارش")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, related_name="order_items", verbose_name="دوره")
    course_code = models.CharField("کد دوره در زمان خرید", max_length=30)
    course_title = models.CharField("عنوان دوره در زمان خرید", max_length=180)
    unit_price = models.PositiveBigIntegerField("قیمت در زمان خرید")

    class Meta:
        verbose_name = "ردیف سفارش"
        verbose_name_plural = "ردیف‌های سفارش"
        constraints = [
            models.UniqueConstraint(fields=["order", "course"], name="uniq_order_course")
        ]

    def __str__(self):
        return f"{self.order.number} / {self.course_title}"


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "INITIATED", "ایجادشده"
        SUCCESS = "SUCCESS", "موفق"
        FAILED = "FAILED", "ناموفق"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment", verbose_name="سفارش")
    amount = models.PositiveBigIntegerField("مبلغ")
    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.INITIATED)
    reference_code = models.CharField("کد پیگیری", max_length=40, unique=True, null=True, blank=True)
    gateway = models.CharField("درگاه", max_length=40, default="SIMULATED")
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    paid_at = models.DateTimeField("پرداخت", null=True, blank=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"

    def __str__(self):
        return f"{self.order.number} - {self.get_status_display()}"


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.PROTECT, related_name="usages", verbose_name="کد تخفیف")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="coupon_usages", verbose_name="کاربر")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="coupon_usage", verbose_name="سفارش")
    used_at = models.DateTimeField("زمان استفاده", auto_now_add=True)

    class Meta:
        verbose_name = "استفاده از تخفیف"
        verbose_name_plural = "استفاده‌های تخفیف"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments", verbose_name="دانشجو")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments", verbose_name="دوره")
    order_item = models.OneToOneField(OrderItem, on_delete=models.PROTECT, related_name="enrollment", verbose_name="ردیف سفارش")
    is_active = models.BooleanField("فعال", default=True)
    progress_percent = models.PositiveSmallIntegerField(
        "درصد پیشرفت", default=0, validators=[MaxValueValidator(100)]
    )
    enrolled_at = models.DateTimeField("زمان ثبت‌نام", auto_now_add=True)
    last_accessed_at = models.DateTimeField("آخرین مراجعه", null=True, blank=True)

    class Meta:
        verbose_name = "دسترسی دوره"
        verbose_name_plural = "دسترسی‌های دوره"
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="uniq_user_course_enrollment")
        ]

    def __str__(self):
        return f"{self.user.email} / {self.course.title}"
