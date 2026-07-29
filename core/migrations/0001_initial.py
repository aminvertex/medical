from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="NewsletterSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="ایمیل")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="عضویت")),
            ],
            options={"verbose_name": "عضو خبرنامه", "verbose_name_plural": "اعضای خبرنامه"},
        ),
        migrations.CreateModel(
            name="ContactMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, verbose_name="نام")),
                ("email", models.EmailField(max_length=254, verbose_name="ایمیل")),
                ("subject", models.CharField(max_length=200, verbose_name="موضوع")),
                ("message", models.TextField(verbose_name="متن پیام")),
                ("status", models.CharField(choices=[("NEW", "جدید"), ("READ", "خوانده‌شده"), ("REPLIED", "پاسخ‌داده‌شده")], db_index=True, default="NEW", max_length=20, verbose_name="وضعیت")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="ثبت")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="contact_messages", to=settings.AUTH_USER_MODEL, verbose_name="کاربر")),
            ],
            options={"verbose_name": "پیام تماس", "verbose_name_plural": "پیام‌های تماس", "ordering": ["-created_at"]},
        ),
    ]
