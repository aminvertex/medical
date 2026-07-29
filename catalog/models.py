from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("نام", max_length=100, unique=True)
    slug = models.SlugField("نامک", max_length=120, unique=True, allow_unicode=True)
    description = models.TextField("توضیحات", blank=True)
    is_active = models.BooleanField("فعال", default=True)
    sort_order = models.PositiveSmallIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "BEGINNER", "مقدماتی"
        INTERMEDIATE = "INTERMEDIATE", "متوسط"
        ADVANCED = "ADVANCED", "پیشرفته"

    code = models.CharField("کد دوره", max_length=30, unique=True)
    title = models.CharField("عنوان", max_length=180)
    slug = models.SlugField("نامک", max_length=220, unique=True, allow_unicode=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="courses", verbose_name="دسته‌بندی")
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="taught_courses",
        limit_choices_to={"role__in": ["INSTRUCTOR", "ADMIN"]},
        verbose_name="مدرس",
    )
    short_description = models.CharField("توضیح کوتاه", max_length=320)
    description = models.TextField("توضیحات کامل")
    price = models.PositiveBigIntegerField("قیمت (تومان)")
    previous_price = models.PositiveBigIntegerField("قیمت قبل", null=True, blank=True)
    duration_hours = models.DecimalField("مدت (ساعت)", max_digits=6, decimal_places=1, default=1)
    level = models.CharField("سطح", max_length=20, choices=Level.choices, default=Level.BEGINNER)
    image = models.FileField("تصویر", upload_to="courses/", blank=True)
    image_path = models.CharField("تصویر ثابت", max_length=255, blank=True)
    is_active = models.BooleanField("فعال", default=True, db_index=True)
    is_featured = models.BooleanField("ویژه", default=False)
    is_bestseller = models.BooleanField("پرفروش", default=False)
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("ویرایش", auto_now=True)

    class Meta:
        verbose_name = "دوره"
        verbose_name_plural = "دوره‌ها"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "category"], name="course_active_cat_idx"),
            models.Index(fields=["is_featured", "is_bestseller"], name="course_flags_idx"),
        ]
        permissions = [
            ("publish_course", "Can publish or unpublish course"),
            ("view_sales_report", "Can view course sales report"),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return self.image_path or "/static/assets/logonomy-1763455510995.png"

    @property
    def discount_percent(self):
        if self.previous_price and self.previous_price > self.price:
            return round((self.previous_price - self.price) * 100 / self.previous_price)
        return 0


class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections", verbose_name="دوره")
    title = models.CharField("عنوان فصل", max_length=180)
    order = models.PositiveSmallIntegerField("ترتیب", default=1)

    class Meta:
        verbose_name = "فصل دوره"
        verbose_name_plural = "فصل‌های دوره"
        ordering = ["course", "order"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="uniq_course_section_order")
        ]

    def __str__(self):
        return f"{self.course.title} / {self.title}"


class Lesson(models.Model):
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="lessons", verbose_name="فصل")
    title = models.CharField("عنوان درس", max_length=180)
    duration_minutes = models.PositiveSmallIntegerField("مدت (دقیقه)", default=10)
    order = models.PositiveSmallIntegerField("ترتیب", default=1)
    is_preview = models.BooleanField("پیش‌نمایش رایگان", default=False)

    class Meta:
        verbose_name = "درس"
        verbose_name_plural = "درس‌ها"
        ordering = ["section", "order"]
        constraints = [
            models.UniqueConstraint(fields=["section", "order"], name="uniq_section_lesson_order")
        ]

    def __str__(self):
        return self.title


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "در انتظار بررسی"
        APPROVED = "APPROVED", "تأییدشده"
        REJECTED = "REJECTED", "ردشده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews", verbose_name="کاربر")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews", verbose_name="دوره")
    rating = models.PositiveSmallIntegerField("امتیاز", validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField("نظر")
    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)
    updated_at = models.DateTimeField("ویرایش", auto_now=True)

    class Meta:
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="uniq_user_course_review")
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.course.title} ({self.rating})"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites", verbose_name="کاربر")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="favorited_by", verbose_name="دوره")
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "علاقه‌مندی"
        verbose_name_plural = "علاقه‌مندی‌ها"
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="uniq_user_course_favorite")
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.course.code}"
