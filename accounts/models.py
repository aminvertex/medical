from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("ایمیل الزامی است.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", User.Role.STUDENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("مدیر ارشد باید is_staff=True داشته باشد.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("مدیر ارشد باید is_superuser=True داشته باشد.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "دانشجو"
        INSTRUCTOR = "INSTRUCTOR", "مدرس"
        ADMIN = "ADMIN", "مدیر"

    email = models.EmailField("ایمیل", unique=True)
    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی", max_length=100)
    phone = models.CharField("شماره موبایل", max_length=15, unique=True, null=True, blank=True)
    role = models.CharField("نقش", max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    is_active = models.BooleanField("فعال", default=True)
    is_staff = models.BooleanField("دسترسی پنل Django", default=False)
    date_joined = models.DateTimeField("تاریخ عضویت", default=timezone.now)
    updated_at = models.DateTimeField("آخرین ویرایش", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role", "is_active"], name="user_role_active_idx"),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.email

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def save(self, *args, **kwargs):
        self.email = self.email.lower().strip()
        self.phone = self.phone.strip() if self.phone else None
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False

        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            kwargs["update_fields"] = set(update_fields) | {"email", "phone", "is_staff"}
        super().save(*args, **kwargs)


class InstructorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
        verbose_name="کاربر مدرس",
    )
    title = models.CharField("عنوان تخصصی", max_length=160)
    bio = models.TextField("زندگی‌نامه کوتاه")
    expertise = models.CharField("حوزه تخصص", max_length=220)
    avatar = models.FileField("تصویر", upload_to="instructors/", blank=True)
    avatar_path = models.CharField("تصویر ثابت", max_length=255, blank=True)
    linkedin_url = models.URLField("لینکدین", blank=True)
    website_url = models.URLField("وب‌سایت", blank=True)
    is_featured = models.BooleanField("نمایش در صفحه اصلی", default=False)

    class Meta:
        verbose_name = "پروفایل مدرس"
        verbose_name_plural = "پروفایل مدرس‌ها"
        ordering = ["user__last_name"]

    def __str__(self):
        return self.user.full_name

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return self.avatar_path or "/static/assets/logonomy-1763455510995.png"
