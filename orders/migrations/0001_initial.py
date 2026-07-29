import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True, verbose_name="کد")),
                ("title", models.CharField(max_length=120, verbose_name="عنوان")),
                ("discount_percent", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)], verbose_name="درصد تخفیف")),
                ("min_order_amount", models.PositiveBigIntegerField(default=0, verbose_name="حداقل مبلغ سفارش")),
                ("max_discount_amount", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="سقف تخفیف")),
                ("starts_at", models.DateTimeField(verbose_name="شروع")),
                ("ends_at", models.DateTimeField(verbose_name="پایان")),
                ("usage_limit", models.PositiveIntegerField(blank=True, null=True, verbose_name="سقف استفاده کل")),
                ("per_user_limit", models.PositiveSmallIntegerField(default=1, verbose_name="سقف استفاده هر کاربر")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
            ],
            options={"verbose_name": "کد تخفیف", "verbose_name_plural": "کدهای تخفیف"},
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="ویرایش")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="cart", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={"verbose_name": "سبد خرید", "verbose_name_plural": "سبدهای خرید"},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(editable=False, max_length=32, unique=True, verbose_name="شماره سفارش")),
                ("status", models.CharField(choices=[("PENDING", "در انتظار پرداخت"), ("PAID", "پرداخت‌شده"), ("CANCELLED", "لغوشده"), ("REFUNDED", "بازگشت وجه")], db_index=True, default="PENDING", max_length=20, verbose_name="وضعیت")),
                ("subtotal", models.PositiveBigIntegerField(verbose_name="جمع اولیه")),
                ("discount_amount", models.PositiveBigIntegerField(default=0, verbose_name="مبلغ تخفیف")),
                ("total_amount", models.PositiveBigIntegerField(verbose_name="مبلغ نهایی")),
                ("customer_first_name", models.CharField(max_length=80, verbose_name="نام خریدار")),
                ("customer_last_name", models.CharField(max_length=100, verbose_name="نام خانوادگی خریدار")),
                ("customer_email", models.EmailField(max_length=254, verbose_name="ایمیل خریدار")),
                ("customer_phone", models.CharField(max_length=15, verbose_name="موبایل خریدار")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ثبت")),
                ("paid_at", models.DateTimeField(blank=True, null=True, verbose_name="پرداخت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="ویرایش")),
                ("coupon", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="orders.coupon", verbose_name="کد تخفیف")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to=settings.AUTH_USER_MODEL, verbose_name="مشتری")),
            ],
            options={
                "verbose_name": "سفارش",
                "verbose_name_plural": "سفارش‌ها",
                "ordering": ["-created_at"],
                "permissions": [("view_sales_dashboard", "Can view sales dashboard"), ("refund_order", "Can refund paid order")],
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added_at", models.DateTimeField(auto_now_add=True, verbose_name="افزوده‌شده")),
                ("cart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.cart", verbose_name="سبد")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cart_items", to="catalog.course", verbose_name="دوره")),
            ],
            options={"verbose_name": "ردیف سبد", "verbose_name_plural": "ردیف‌های سبد", "ordering": ["added_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_code", models.CharField(max_length=30, verbose_name="کد دوره در زمان خرید")),
                ("course_title", models.CharField(max_length=180, verbose_name="عنوان دوره در زمان خرید")),
                ("unit_price", models.PositiveBigIntegerField(verbose_name="قیمت در زمان خرید")),
                ("course", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_items", to="catalog.course", verbose_name="دوره")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order", verbose_name="سفارش")),
            ],
            options={"verbose_name": "ردیف سفارش", "verbose_name_plural": "ردیف‌های سفارش"},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.PositiveBigIntegerField(verbose_name="مبلغ")),
                ("status", models.CharField(choices=[("INITIATED", "ایجادشده"), ("SUCCESS", "موفق"), ("FAILED", "ناموفق")], default="INITIATED", max_length=20, verbose_name="وضعیت")),
                ("reference_code", models.CharField(blank=True, max_length=40, null=True, unique=True, verbose_name="کد پیگیری")),
                ("gateway", models.CharField(default="SIMULATED", max_length=40, verbose_name="درگاه")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
                ("paid_at", models.DateTimeField(blank=True, null=True, verbose_name="پرداخت")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="orders.order", verbose_name="سفارش")),
            ],
            options={"verbose_name": "پرداخت", "verbose_name_plural": "پرداخت‌ها"},
        ),
        migrations.CreateModel(
            name="CouponUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("used_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان استفاده")),
                ("coupon", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="usages", to="orders.coupon", verbose_name="کد تخفیف")),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="coupon_usage", to="orders.order", verbose_name="سفارش")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="coupon_usages", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={"verbose_name": "استفاده از تخفیف", "verbose_name_plural": "استفاده‌های تخفیف"},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("progress_percent", models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)], verbose_name="درصد پیشرفت")),
                ("enrolled_at", models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت‌نام")),
                ("last_accessed_at", models.DateTimeField(blank=True, null=True, verbose_name="آخرین مراجعه")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="catalog.course", verbose_name="دوره")),
                ("order_item", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="enrollment", to="orders.orderitem", verbose_name="ردیف سفارش")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL, verbose_name="دانشجو")),
            ],
            options={"verbose_name": "دسترسی دوره", "verbose_name_plural": "دسترسی‌های دوره"},
        ),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["status", "created_at"], name="order_status_date_idx")),
        migrations.AddIndex(model_name="order", index=models.Index(fields=["user", "status"], name="order_user_status_idx")),
        migrations.AddConstraint(model_name="cartitem", constraint=models.UniqueConstraint(fields=("cart", "course"), name="uniq_cart_course")),
        migrations.AddConstraint(model_name="orderitem", constraint=models.UniqueConstraint(fields=("order", "course"), name="uniq_order_course")),
        migrations.AddConstraint(model_name="enrollment", constraint=models.UniqueConstraint(fields=("user", "course"), name="uniq_user_course_enrollment")),
    ]
