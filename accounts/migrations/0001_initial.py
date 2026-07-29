import accounts.models
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="ایمیل")),
                ("first_name", models.CharField(max_length=80, verbose_name="نام")),
                ("last_name", models.CharField(max_length=100, verbose_name="نام خانوادگی")),
                ("phone", models.CharField(blank=True, max_length=15, null=True, unique=True, verbose_name="شماره موبایل")),
                ("role", models.CharField(choices=[("STUDENT", "دانشجو"), ("INSTRUCTOR", "مدرس"), ("ADMIN", "مدیر")], db_index=True, default="STUDENT", max_length=20, verbose_name="نقش")),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال")),
                ("is_staff", models.BooleanField(default=False, verbose_name="دسترسی پنل Django")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="تاریخ عضویت")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "کاربر",
                "verbose_name_plural": "کاربران",
                "ordering": ["-date_joined"],
            },
            managers=[("objects", accounts.models.UserManager())],
        ),
        migrations.CreateModel(
            name="InstructorProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="عنوان تخصصی")),
                ("bio", models.TextField(verbose_name="زندگی‌نامه کوتاه")),
                ("expertise", models.CharField(max_length=220, verbose_name="حوزه تخصص")),
                ("avatar", models.FileField(blank=True, upload_to="instructors/", verbose_name="تصویر")),
                ("avatar_path", models.CharField(blank=True, max_length=255, verbose_name="تصویر ثابت")),
                ("linkedin_url", models.URLField(blank=True, verbose_name="لینکدین")),
                ("website_url", models.URLField(blank=True, verbose_name="وب‌سایت")),
                ("is_featured", models.BooleanField(default=False, verbose_name="نمایش در صفحه اصلی")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="instructor_profile", to="accounts.user", verbose_name="کاربر مدرس")),
            ],
            options={
                "verbose_name": "پروفایل مدرس",
                "verbose_name_plural": "پروفایل مدرس‌ها",
                "ordering": ["user__last_name"],
            },
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["role", "is_active"], name="user_role_active_idx"),
        ),
    ]
