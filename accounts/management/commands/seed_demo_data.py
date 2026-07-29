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
            email="admin@nersimed.ir",
            password="Admin12345!",
            first_name="مدیر",
            last_name="سامانه",
            phone="09120000001",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        instructor = self._upsert_user(
            email="dr.rezaei@nersimed.ir",
            password="Teacher12345!",
            first_name="دکتر محمد",
            last_name="رضایی",
            phone="09120000002",
            role=User.Role.INSTRUCTOR,
        )
        instructor_two = self._upsert_user(
            email="dr.ahmadi@nersimed.ir",
            password="Teacher12345!",
            first_name="دکتر سارا",
            last_name="احمدی",
            phone="09120000003",
            role=User.Role.INSTRUCTOR,
        )
        student = self._upsert_user(
            email="student@nersimed.ir",
            password="Student12345!",
            first_name="علی",
            last_name="دانشجو",
            phone="09120000004",
            role=User.Role.STUDENT,
        )

        InstructorProfile.objects.update_or_create(
            user=instructor,
            defaults={
                "title": "متخصص قلب و عروق - فلوشیپ اینترونشنال کاردیولوژی",
                "bio": "عضو هیئت علمی دانشگاه علوم پزشکی تهران با بیش از ۱۵ سال تجربه در زمینه آموزش پزشکی و درمان بیماری‌های قلبی.",
                "expertise": "قلب و عروق، اکوکاردیوگرافی، آنژیوگرافی",
                "avatar_path": "/static/assets/dr-rezaei.jpg",
                "is_featured": True,
            },
        )
        InstructorProfile.objects.update_or_create(
            user=instructor_two,
            defaults={
                "title": "متخصص مغز و اعصاب - فلوشیپ نورولوژی مداخله‌ای",
                "bio": "پژوهشگر و مدرس برجسته در حوزه علوم اعصاب با تمرکز بر آموزش بالینی و مهارت‌های عملی.",
                "expertise": "مغز و اعصاب، EEG، EMG، سکته مغزی",
                "avatar_path": "/static/assets/dr-ahmadi.jpg",
                "is_featured": True,
            },
        )

        categories = {
            "cardiology": self._category("قلب و عروق", "cardiology", 1),
            "neurology": self._category("مغز و اعصاب", "neurology", 2),
            "internal": self._category("داخلی", "internal-medicine", 3),
            "surgery": self._category("جراحی عمومی", "general-surgery", 4),
            "pediatrics": self._category("اطفال", "pediatrics", 5),
            "dermatology": self._category("پوست و مو", "dermatology", 6),
            "emergency": self._category("اورژانس", "emergency-medicine", 7),
            "radiology": self._category("رادیولوژی", "radiology", 8),
            "psychiatry": self._category("روانپزشکی", "psychiatry", 9),
            "anesthesia": self._category("بیهوشی", "anesthesiology", 10),
            "orthopedics": self._category("ارتوپدی", "orthopedics", 11),
            "pharmacy": self._category("داروسازی", "pharmacy", 12),
            "nursing": self._category("پرستاری", "nursing", 13),
            "lab": self._category("آزمایشگاه", "laboratory", 14),
            "basic": self._category("علوم پایه پزشکی", "basic-medical-sciences", 15),
        }

        course_specs = [
            {
                "code": "MED-CARD-101",
                "title": "اکوکاردیوگرافی مقدماتی (Basic Echocardiography)",
                "slug": "basic-echocardiography",
                "category": categories["cardiology"],
                "instructor": instructor,
                "short_description": "آموزش جامع اصول اکوکاردیوگرافی ترانس‌توراسیک با رویکرد بالینی و عملی.",
                "description": "این دوره شما را با مبانی فیزیک اولتراسوند، آناتومی اکوکاردیوگرافی، پروتکل‌های اسکن استاندارد و تفسیر یافته‌های طبیعی و پاتولوژیک آشنا می‌کند.",
                "price": 3_490_000,
                "previous_price": 4_200_000,
                "duration_hours": 28,
                "level": Course.Level.INTERMEDIATE,
                "image_path": "/static/assets/echo-course.jpg",
                "is_featured": True,
                "is_bestseller": True,
                "sections": [
                    ("مبانی فیزیک و آناتومی", ["اصول امواج اولتراسوند", "آناتومی چهارحفره‌ای قلب", "پوزیشن‌های استاندارد پروب"]),
                    ("پروتکل اسکن کامل", ["نمای پاراسترنال", "نمای آپیکال", "نمای ساب‌کوستال", "اندازه‌گیری‌های استاندارد"]),
                ],
            },
            {
                "code": "MED-NEURO-201",
                "title": "تفسیر نوار مغز (EEG Interpretation)",
                "slug": "eeg-interpretation",
                "category": categories["neurology"],
                "instructor": instructor_two,
                "short_description": "دوره جامع تفسیر الکتروانسفالوگرافی برای متخصصان مغز و اعصاب و رزیدنت‌ها.",
                "description": "یادگیری الگوهای طبیعی و پاتولوژیک EEG، شناسایی فعالیت‌های تشنجی، و تفسیر یافته‌های بالینی مرتبط با اختلالات نورولوژیک.",
                "price": 3_990_000,
                "previous_price": 4_650_000,
                "duration_hours": 32,
                "level": Course.Level.ADVANCED,
                "image_path": "/static/assets/eeg-course.jpg",
                "is_featured": True,
                "is_bestseller": True,
                "sections": [
                    ("اصول EEG", ["فیزیولوژی امواج مغزی", "الکترودگذاری 10-20", "کالیبراسیون دستگاه"]),
                    ("الگوهای پاتولوژیک", ["امواج صرعی", "کمپلکس‌های سه فاز", "الگوهای بورست-ساپرس"]),
                ],
            },
            {
                "code": "MED-INT-110",
                "title": "مدیریت دیابت نوع ۲ در مراقبت‌های اولیه",
                "slug": "diabetes-type2-management",
                "category": categories["internal"],
                "instructor": instructor,
                "short_description": "راهنمای جامع تشخیص، درمان و پیگیری بیماران مبتلا به دیابت نوع ۲.",
                "description": "این دوره رویکردهای مبتنی بر شواهد برای مدیریت گلیسمی، پیشگیری از عوارض میکروواسکولار و ماکروواسکولار، و تنظیم رژیم دارویی را پوشش می‌دهد.",
                "price": 2_490_000,
                "previous_price": 2_950_000,
                "duration_hours": 18,
                "level": Course.Level.BEGINNER,
                "image_path": "/static/assets/diabetes-course.jpg",
                "is_featured": True,
                "is_bestseller": False,
                "sections": [
                    ("تشخیص و ارزیابی", ["معیارهای تشخیصی ADA", "غربالگری عوارض", "ارزیابی ریسک قلبی-عروقی"]),
                    ("درمان دارویی", ["متفورمین و مشتقات سولفونیل‌اوره", "GLP-1 RA و SGLT2i", "انسولین‌تراپی"]),
                ],
            },
            {
                "code": "MED-SURG-120",
                "title": "اصول جراحی لاپاراسکوپی (Fundamentals of Laparoscopic Surgery)",
                "slug": "laparoscopic-surgery-basics",
                "category": categories["surgery"],
                "instructor": instructor_two,
                "short_description": "آموزش مهارت‌های پایه جراحی کم‌تهاجمی برای رزیدنت‌های جراحی.",
                "description": "یادگیری اصول ارگونومی، تکنیک‌های کوآگولاسیون، دوخت لاپاراسکوپی، و مدیریت عوارض احتمالی در حین عمل.",
                "price": 4_250_000,
                "previous_price": None,
                "duration_hours": 24,
                "level": Course.Level.INTERMEDIATE,
                "image_path": "/static/assets/laparo-course.jpg",
                "is_featured": True,
                "is_bestseller": False,
                "sections": [
                    ("مبانی و ایمنی", ["تجهیزات لاپاراسکوپی", "ایجاد پنوموپریتونئوم", "پوزیشن‌دهی بیمار"]),
                    ("مهارت‌های عملی", ["دیسکسیون و هموستاز", "کلیپینگ و استاپلینگ", "سuture intracorporeal"]),
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
            code="MEDICAL20",
            defaults={
                "title": "تخفیف ویژه دانشجویان علوم پزشکی",
                "discount_percent": 20,
                "min_order_amount": 1_500_000,
                "max_discount_amount": 800_000,
                "starts_at": now - timedelta(days=30),
                "ends_at": now + timedelta(days=365),
                "usage_limit": 500,
                "per_user_limit": 1,
                "is_active": True,
            },
        )

        order, _ = Order.objects.update_or_create(
            number="NERSIMED-DEMO-0001",
            defaults={
                "user": student,
                "status": Order.Status.PAID,
                "subtotal": courses["MED-CARD-101"].price,
                "discount_amount": 0,
                "total_amount": courses["MED-CARD-101"].price,
                "customer_first_name": student.first_name,
                "customer_last_name": student.last_name,
                "customer_email": student.email,
                "customer_phone": student.phone,
                "paid_at": now - timedelta(days=3),
            },
        )
        item, _ = OrderItem.objects.update_or_create(
            order=order,
            course=courses["MED-CARD-101"],
            defaults={
                "course_code": courses["MED-CARD-101"].code,
                "course_title": courses["MED-CARD-101"].title,
                "unit_price": courses["MED-CARD-101"].price,
            },
        )
        Payment.objects.update_or_create(
            order=order,
            defaults={
                "amount": order.total_amount,
                "status": Payment.Status.SUCCESS,
                "reference_code": "SIM-NERSIMED-0001",
                "gateway": "SIMULATED",
                "paid_at": order.paid_at,
            },
        )
        Enrollment.objects.update_or_create(
            user=student,
            course=courses["MED-CARD-101"],
            defaults={"order_item": item, "is_active": True, "progress_percent": 35},
        )
        Review.objects.update_or_create(
            user=student,
            course=courses["MED-CARD-101"],
            defaults={
                "rating": 5,
                "comment": "کیفیت آموزش اکوکاردیوگرافی عالی بود. دکتر رضایی با صبر و حوصله تمام نکات بالینی را توضیح دادند.",
                "status": Review.Status.APPROVED,
            },
        )
        Favorite.objects.get_or_create(user=student, course=courses["MED-NEURO-201"])
        cart, _ = Cart.objects.get_or_create(user=student)
        CartItem.objects.get_or_create(cart=cart, course=courses["MED-INT-110"])

        ContactMessage.objects.get_or_create(
            email="prospect@example.com",
            subject="سؤال درباره پیش‌نیاز دوره اکوکاردیوگرافی",
            defaults={
                "name": "کاربر مهمان",
                "message": "آیا برای شرکت در دوره اکوکاردیوگرافی نیاز به گذراندن دوره فیزیولوژی قلب داریم؟",
                "status": ContactMessage.Status.NEW,
            },
        )
        NewsletterSubscription.objects.get_or_create(email="student@nersimed.ir")

        self.stdout.write(self.style.SUCCESS("داده‌های نمایشی نرسیمد آکادمی با موفقیت ایجاد/به‌روزرسانی شدند."))
        self.stdout.write("Admin: admin@nersimed.ir / Admin12345!")
        self.stdout.write("Instructor: dr.rezaei@nersimed.ir / Teacher12345!")
        self.stdout.write("Student: student@nersimed.ir / Student12345!")

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
