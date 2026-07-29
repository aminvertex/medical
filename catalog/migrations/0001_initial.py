import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True, verbose_name="نام")),
                ("slug", models.SlugField(allow_unicode=True, max_length=120, unique=True, verbose_name="نامک")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("sort_order", models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب")),
            ],
            options={"verbose_name": "دسته‌بندی", "verbose_name_plural": "دسته‌بندی‌ها", "ordering": ["sort_order", "name"]},
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True, verbose_name="کد دوره")),
                ("title", models.CharField(max_length=180, verbose_name="عنوان")),
                ("slug", models.SlugField(allow_unicode=True, max_length=220, unique=True, verbose_name="نامک")),
                ("short_description", models.CharField(max_length=320, verbose_name="توضیح کوتاه")),
                ("description", models.TextField(verbose_name="توضیحات کامل")),
                ("price", models.PositiveBigIntegerField(verbose_name="قیمت (تومان)")),
                ("previous_price", models.PositiveBigIntegerField(blank=True, null=True, verbose_name="قیمت قبل")),
                ("duration_hours", models.DecimalField(decimal_places=1, default=1, max_digits=6, verbose_name="مدت (ساعت)")),
                ("level", models.CharField(choices=[("BEGINNER", "مقدماتی"), ("INTERMEDIATE", "متوسط"), ("ADVANCED", "پیشرفته")], default="BEGINNER", max_length=20, verbose_name="سطح")),
                ("image", models.FileField(blank=True, upload_to="courses/", verbose_name="تصویر")),
                ("image_path", models.CharField(blank=True, max_length=255, verbose_name="تصویر ثابت")),
                ("is_active", models.BooleanField(db_index=True, default=True, verbose_name="فعال")),
                ("is_featured", models.BooleanField(default=False, verbose_name="ویژه")),
                ("is_bestseller", models.BooleanField(default=False, verbose_name="پرفروش")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ایجاد")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="ویرایش")),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="courses", to="catalog.category", verbose_name="دسته‌بندی")),
                ("instructor", models.ForeignKey(limit_choices_to={"role__in": ["INSTRUCTOR", "ADMIN"]}, on_delete=django.db.models.deletion.PROTECT, related_name="taught_courses", to=settings.AUTH_USER_MODEL, verbose_name="مدرس")),
            ],
            options={
                "verbose_name": "دوره",
                "verbose_name_plural": "دوره‌ها",
                "ordering": ["-created_at"],
                "permissions": [("publish_course", "Can publish or unpublish course"), ("view_sales_report", "Can view course sales report")],
            },
        ),
        migrations.CreateModel(
            name="CourseSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="عنوان فصل")),
                ("order", models.PositiveSmallIntegerField(default=1, verbose_name="ترتیب")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="catalog.course", verbose_name="دوره")),
            ],
            options={"verbose_name": "فصل دوره", "verbose_name_plural": "فصل‌های دوره", "ordering": ["course", "order"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="عنوان درس")),
                ("duration_minutes", models.PositiveSmallIntegerField(default=10, verbose_name="مدت (دقیقه)")),
                ("order", models.PositiveSmallIntegerField(default=1, verbose_name="ترتیب")),
                ("is_preview", models.BooleanField(default=False, verbose_name="پیش‌نمایش رایگان")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="catalog.coursesection", verbose_name="فصل")),
            ],
            options={"verbose_name": "درس", "verbose_name_plural": "درس‌ها", "ordering": ["section", "order"]},
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name="امتیاز")),
                ("comment", models.TextField(verbose_name="نظر")),
                ("status", models.CharField(choices=[("PENDING", "در انتظار بررسی"), ("APPROVED", "تأییدشده"), ("REJECTED", "ردشده")], db_index=True, default="PENDING", max_length=20, verbose_name="وضعیت")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ثبت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="ویرایش")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="catalog.course", verbose_name="دوره")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={"verbose_name": "نظر", "verbose_name_plural": "نظرات", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Favorite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ثبت")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorited_by", to="catalog.course", verbose_name="دوره")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="favorites", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={"verbose_name": "علاقه‌مندی", "verbose_name_plural": "علاقه‌مندی‌ها"},
        ),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["is_active", "category"], name="course_active_cat_idx")),
        migrations.AddIndex(model_name="course", index=models.Index(fields=["is_featured", "is_bestseller"], name="course_flags_idx")),
        migrations.AddConstraint(model_name="coursesection", constraint=models.UniqueConstraint(fields=("course", "order"), name="uniq_course_section_order")),
        migrations.AddConstraint(model_name="lesson", constraint=models.UniqueConstraint(fields=("section", "order"), name="uniq_section_lesson_order")),
        migrations.AddConstraint(model_name="review", constraint=models.UniqueConstraint(fields=("user", "course"), name="uniq_user_course_review")),
        migrations.AddConstraint(model_name="favorite", constraint=models.UniqueConstraint(fields=("user", "course"), name="uniq_user_course_favorite")),
    ]
