from django.conf import settings
from django.db import models


class ContactMessage(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "جدید"
        READ = "READ", "خوانده‌شده"
        REPLIED = "REPLIED", "پاسخ‌داده‌شده"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="contact_messages", verbose_name="کاربر")
    name = models.CharField("نام", max_length=160)
    email = models.EmailField("ایمیل")
    subject = models.CharField("موضوع", max_length=200)
    message = models.TextField("متن پیام")
    status = models.CharField("وضعیت", max_length=20, choices=Status.choices, default=Status.NEW, db_index=True)
    created_at = models.DateTimeField("ثبت", auto_now_add=True)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} - {self.email}"


class NewsletterSubscription(models.Model):
    email = models.EmailField("ایمیل", unique=True)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("عضویت", auto_now_add=True)

    class Meta:
        verbose_name = "عضو خبرنامه"
        verbose_name_plural = "اعضای خبرنامه"

    def __str__(self):
        return self.email
