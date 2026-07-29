from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import InstructorProfile, User
from catalog.models import Category, Course, CourseSection, Favorite, Lesson, Review
from core.models import ContactMessage, NewsletterSubscription
from orders.models import Cart, CartItem, Coupon, Enrollment, Order, OrderItem, Payment


class Command(BaseCommand):
    help = "داده‌های نمایشی و حساب‌های آماده ارائه را به‌صورت idempotent ایجاد می‌کند."

    @transaction.atomic
    def handle(self, *args, **options):
        admin = self._upsert_user(
            email="admin@mahdai.ir",
            password="Admin12345!",
            first_name="مدیر",
            last_name="سامانه",
            phone="09120000001",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        instructor = self._upsert_user(
            email="instructor@mahdai.ir",
            password="Teacher12345!",
            first_name="محمد",
            last_name="رضایی",
            phone="09120000002",
            role=User.Role.INSTRUCTOR,
        )
        instructor_two = self._upsert_user(
            email="instructor2@mahdai.ir",
            password="Teacher12345!",
            first_name="سارا",
            last_name="احمدی",
            phone="09120000003",
            role=User.Role.INSTRUCTOR,
        )
        student = self._upsert_user(
            email="student@mahdai.ir",
            password="Student12345!",
            first_name="علی",
            last_name="دانشجو",
            phone="09120000004",
            role=User.Role.STUDENT,
        )

        InstructorProfile.objects.update_or_create(
            user=instructor,
            defaults={
                "title": "مدرس یادگیری ماشین و علم داده",
                "bio": "متخصص داده و هوش مصنوعی با تجربه اجرای پروژه‌های صنعتی و آموزش پروژه‌محور.",
                "expertise": "یادگیری ماشین، پایتون و تحلیل داده",
                "avatar_path": "/static/assets/مهندس-محمد-رضایی-وب-سایت.jpg",
                "is_featured": True,
            },
        )
        InstructorProfile.objects.update_or_create(
            user=instructor_two,
            defaults={
                "title": "مدرس یادگیری عمیق و پردازش زبان",
                "bio": "پژوهشگر شبکه‌های عصبی و توسعه‌دهنده راهکارهای هوش مصنوعی مولد.",
                "expertise": "یادگیری عمیق، NLP و هوش مصنوعی مولد",
                "avatar_path": "/static/assets/images (1).jpg",
                "is_featured": True,
            },
        )

        categories = {
            "ml": self._category("یادگیری ماشین", "machine-learning", 1),
            "dl": self._category("یادگیری عمیق", "deep-learning", 2),
            "nlp": self._category("پردازش زبان طبیعی", "nlp", 3),
            "data": self._category("علم داده", "data-science", 4),
        }

        course_specs = [
            {
                "code": "AI-ML-101",
                "title": "یادگیری ماشین (Machine Learning)",
                "slug": "machine-learning",
                "category": categories["ml"],
                "instructor": instructor,
                "short_description": "آموزش مفاهیم پایه و الگوریتم‌های پرکاربرد یادگیری ماشین با پروژه‌های واقعی.",
                "description": "از آماده‌سازی داده تا آموزش، ارزیابی و ارائه مدل‌های یادگیری ماشین را در یک مسیر پروژه‌محور یاد می‌گیرید.",
                "price": 2_490_000,
                "previous_price": 2_900_000,
                "duration_hours": 24,
                "level": Course.Level.INTERMEDIATE,
                "image_path": "/static/assets/mas.png",
                "is_featured": True,
                "is_bestseller": True,
                "sections": [
                    ("مبانی و آماده‌سازی داده", ["آشنایی با مسیر پروژه", "پاک‌سازی و پیش‌پردازش داده", "تقسیم داده آموزشی و آزمون"]),
                    ("الگوریتم‌های نظارت‌شده", ["رگرسیون", "درخت تصمیم", "ارزیابی و تنظیم مدل"]),
                ],
            },
            {
                "code": "AI-DL-201",
                "title": "یادگیری عمیق (Deep Learning)",
                "slug": "deep-learning",
                "category": categories["dl"],
                "instructor": instructor_two,
                "short_description": "شبکه‌های عصبی، CNN و مدل‌های عمیق را با تمرین و پروژه عملی فرا بگیرید.",
                "description": "ساخت شبکه عصبی از پایه، آموزش مدل‌های بینایی و مدیریت فرایند آزمایش با تمرکز بر درک معماری‌ها.",
                "price": 2_990_000,
                "previous_price": 3_450_000,
                "duration_hours": 30,
                "level": Course.Level.ADVANCED,
                "image_path": "/static/assets/yad.png",
                "is_featured": True,
                "is_bestseller": True,
                "sections": [
                    ("شبکه‌های عصبی", ["نورون و تابع فعال‌سازی", "پس‌انتشار خطا", "بهینه‌سازها"]),
                    ("بینایی ماشین", ["شبکه‌های کانولوشنی", "افزایش داده", "پروژه دسته‌بندی تصویر"]),
                ],
            },
            {
                "code": "AI-GEN-110",
                "title": "ساخت چت‌بات با ChatGPT API",
                "slug": "chatgpt-api",
                "category": categories["nlp"],
                "instructor": instructor_two,
                "short_description": "ساخت چت‌بات‌های هوشمند و اتصال مدل زبانی به یک برنامه واقعی.",
                "description": "اصول طراحی پرامپت، مدیریت گفتگو، اتصال API و ساخت یک نمونه کاربردی قابل ارائه را تجربه می‌کنید.",
                "price": 1_990_000,
                "previous_price": 2_350_000,
                "duration_hours": 14,
                "level": Course.Level.BEGINNER,
                "image_path": "/static/assets/sakg.png",
                "is_featured": True,
                "is_bestseller": False,
                "sections": [
                    ("شروع کار با مدل‌های زبانی", ["مفاهیم پایه LLM", "ساختار درخواست و پاسخ", "مدیریت خطا"]),
                    ("پروژه چت‌بات", ["حافظه گفتگو", "اتصال رابط کاربری", "آماده‌سازی نسخه نهایی"]),
                ],
            },
            {
                "code": "AI-DATA-120",
                "title": "داده‌کاوی و تحلیل داده با پایتون",
                "slug": "data-mining-python",
                "category": categories["data"],
                "instructor": instructor,
                "short_description": "تحلیل داده، کشف الگو و گزارش‌سازی با ابزارهای کاربردی پایتون.",
                "description": "با یک مجموعه‌داده واقعی کار می‌کنید و از پاک‌سازی تا تحلیل اکتشافی و ارائه نتیجه پیش می‌روید.",
                "price": 2_450_000,
                "previous_price": None,
                "duration_hours": 20,
                "level": Course.Level.BEGINNER,
                "image_path": "/static/assets/dad.png",
                "is_featured": True,
                "is_bestseller": False,
                "sections": [
                    ("تحلیل اکتشافی", ["کار با DataFrame", "پاک‌سازی داده", "نمودار و تفسیر"]),
                    ("کشف الگو", ["خوشه‌بندی", "قواعد انجمنی", "پروژه پایانی"]),
                ],
            },
        ]

        courses = {}
        for spec in course_specs:
            sections = spec.pop("sections")
            course, _ = Course.objects.update_or_create(code=spec["code"], defaults=spec)
            courses[course.code] = course
            self._sections(course, sections)

        now = timezone.now()
        Coupon.objects.update_or_create(
            code="AI20",
            defaults={
                "title": "تخفیف ارائه دانشگاهی",
                "discount_percent": 20,
                "min_order_amount": 1_000_000,
                "max_discount_amount": 600_000,
                "starts_at": now - timedelta(days=30),
                "ends_at": now + timedelta(days=365),
                "usage_limit": 500,
                "per_user_limit": 1,
                "is_active": True,
            },
        )

        order, _ = Order.objects.update_or_create(
            number="MAH-DEMO-0001",
            defaults={
                "user": student,
                "status": Order.Status.PAID,
                "subtotal": courses["AI-ML-101"].price,
                "discount_amount": 0,
                "total_amount": courses["AI-ML-101"].price,
                "customer_first_name": student.first_name,
                "customer_last_name": student.last_name,
                "customer_email": student.email,
                "customer_phone": student.phone,
                "paid_at": now - timedelta(days=3),
            },
        )
        item, _ = OrderItem.objects.update_or_create(
            order=order,
            course=courses["AI-ML-101"],
            defaults={
                "course_code": courses["AI-ML-101"].code,
                "course_title": courses["AI-ML-101"].title,
                "unit_price": courses["AI-ML-101"].price,
            },
        )
        Payment.objects.update_or_create(
            order=order,
            defaults={
                "amount": order.total_amount,
                "status": Payment.Status.SUCCESS,
                "reference_code": "SIM-DEMO-0001",
                "gateway": "SIMULATED",
                "paid_at": order.paid_at,
            },
        )
        Enrollment.objects.update_or_create(
            user=student,
            course=courses["AI-ML-101"],
            defaults={"order_item": item, "is_active": True, "progress_percent": 35},
        )
        Review.objects.update_or_create(
            user=student,
            course=courses["AI-ML-101"],
            defaults={
                "rating": 5,
                "comment": "ساختار دوره روشن بود و پروژه پایانی برای ارائه دانشگاهی خیلی کمک کرد.",
                "status": Review.Status.APPROVED,
            },
        )
        Favorite.objects.get_or_create(user=student, course=courses["AI-DL-201"])
        cart, _ = Cart.objects.get_or_create(user=student)
        CartItem.objects.get_or_create(cart=cart, course=courses["AI-GEN-110"])

        ContactMessage.objects.get_or_create(
            email="prospect@example.com",
            subject="سؤال درباره پیش‌نیاز دوره",
            defaults={
                "name": "کاربر مهمان",
                "message": "برای شروع دوره یادگیری ماشین چه مقدار پایتون باید بلد باشم؟",
                "status": ContactMessage.Status.NEW,
            },
        )
        NewsletterSubscription.objects.get_or_create(email="student@mahdai.ir")

        self.stdout.write(self.style.SUCCESS("داده‌های نمایشی MAHDAI با موفقیت ایجاد/به‌روزرسانی شدند."))
        self.stdout.write("Admin: admin@mahdai.ir / Admin12345!")
        self.stdout.write("Instructor: instructor@mahdai.ir / Teacher12345!")
        self.stdout.write("Student: student@mahdai.ir / Student12345!")

    def _upsert_user(self, *, email, password, first_name, last_name, phone, role, is_staff=False, is_superuser=False):
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "role": role,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        user.set_password(password)
        user.save()
        return user

    def _category(self, name, slug, sort_order):
        return Category.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "description": f"دوره‌های حوزه {name}", "is_active": True, "sort_order": sort_order},
        )[0]

    def _sections(self, course, sections):
        for section_order, (section_title, lessons) in enumerate(sections, start=1):
            section, _ = CourseSection.objects.update_or_create(
                course=course,
                order=section_order,
                defaults={"title": section_title},
            )
            for lesson_order, lesson_title in enumerate(lessons, start=1):
                Lesson.objects.update_or_create(
                    section=section,
                    order=lesson_order,
                    defaults={
                        "title": lesson_title,
                        "duration_minutes": 25 + lesson_order * 5,
                        "is_preview": section_order == 1 and lesson_order == 1,
                    },
                )
