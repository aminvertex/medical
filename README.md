# MAHDAI Academy — فروشگاه دوره‌های هوش مصنوعی با Django Ninja

این مخزن نسخهٔ کامل‌شدهٔ پروژهٔ فرانت دانشگاهی **MAHDAI** است. فرانت استاتیک اولیه حفظ شده و به یک سامانهٔ واقعی فروش دوره با Django، Django Ninja، SQLite، احراز هویت Session، نقش‌ها، سبد خرید، سفارش، پرداخت شبیه‌سازی‌شده، گزارش فروش و پنل مدیریت تبدیل شده است.

## قابلیت‌های اصلی

- ثبت‌نام با نام، نام خانوادگی، ایمیل، موبایل و رمز عبور
- ورود و خروج امن مبتنی بر Session و Cookie
- سه نقش `STUDENT`، `INSTRUCTOR` و `ADMIN`
- پاسخ واقعی `403 Forbidden` برای کاربر واردشده‌ای که نقش کافی ندارد
- فروشگاه پویا با جست‌وجو، دسته‌بندی و مرتب‌سازی
- مدیریت دوره، فصل و درس
- سبد خرید واقعی در SQLite با جلوگیری از افزودن تکراری
- ثبت سفارش با Snapshot قیمت و عنوان دوره در زمان خرید
- کد تخفیف با بازه زمانی، سقف استفاده و حداقل مبلغ
- پرداخت آزمایشی با کد پیگیری و فعال‌سازی خودکار دوره
- سفارش‌های من، دوره‌های من و علاقه‌مندی‌های من
- ثبت نظر فقط برای خریدار دوره و انتشار پس از تأیید مدیر
- فرم تماس و خبرنامه متصل به دیتابیس
- داشبورد سفارشی مدیر و پنل استاندارد Django Admin
- پنل مدرس با آمار دوره‌های منتسب به همان مدرس
- API مستندشده با Swagger در `/api/docs`
- دادهٔ نمایشی idempotent برای ارائه سریع دانشگاهی

## اجرای سریع بدون Docker

ساده‌ترین روش در Linux/macOS:

```bash
./setup.sh
./start.sh
```

در Windows:

```bat
setup_windows.bat
start_windows.bat
```

روش دستی:

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

سپس آدرس زیر را باز کنید:

```text
http://127.0.0.1:8000/
```

## حساب‌های آماده ارائه

| نقش | ایمیل | رمز عبور |
|---|---|---|
| مدیر | `admin@mahdai.ir` | `Admin12345!` |
| مدرس | `instructor@mahdai.ir` | `Teacher12345!` |
| دانشجو | `student@mahdai.ir` | `Student12345!` |

کد تخفیف نمایشی: `AI20`

> دستور `seed_demo_data` قابل تکرار است و اجرای دوبارهٔ آن داده‌های تکراری نمی‌سازد.

## مسیرهای مهم

| بخش | مسیر |
|---|---|
| صفحه اصلی | `/` |
| فروشگاه | `/shop/` |
| ورود و ثبت‌نام | `/auth/` |
| سبد خرید | `/cart/` |
| تسویه‌حساب | `/checkout/` |
| حساب کاربری | `/account/` |
| سفارش‌های من | `/account/orders/` |
| دوره‌های من | `/account/courses/` |
| داشبورد مدیر | `/dashboard/` |
| پنل مدرس | `/instructor/` |
| Django Admin | `/django-admin/` |
| Swagger API | `/api/docs` |

جدول کامل Routeها در [`docs/ROUTES_FA.md`](docs/ROUTES_FA.md) قرار دارد.

## ساختار پروژه

```text
MAHDAI/
├── accounts/          # کاربر سفارشی، Session Auth، نقش‌ها و صفحات حساب
├── catalog/           # دسته‌بندی، دوره، فصل، درس، نظر و علاقه‌مندی
├── orders/            # سبد، سفارش، ردیف سفارش، پرداخت، تخفیف و Enrollment
├── core/              # خانه، تماس، خبرنامه و صفحات عمومی
├── dashboard/         # داشبورد مدیر و مدرس و APIهای مدیریتی
├── config/            # تنظیمات، URLهای اصلی و NinjaAPI
├── templates/         # قالب‌های Django و Partialهای مشترک
├── static/            # CSS، JavaScript و تصاویر
├── media/             # فایل‌های آپلودشده توسط مدیر
├── legacy_frontend/   # نسخهٔ اصلی فرانت، بدون حذف یا دست‌کاری
├── docs/              # معماری، ERD، Routeها و راهنمای ارائه
└── db.sqlite3         # پس از migrate ساخته می‌شود
```

## نقش‌ها و دسترسی‌ها

### دانشجو

مشاهده دوره‌ها، مدیریت سبد، خرید، مشاهده سفارش‌ها و دوره‌های خودش، علاقه‌مندی و ثبت نظر برای دورهٔ خریداری‌شده.

### مدرس

تمام قابلیت‌های عمومی، به‌علاوه مشاهدهٔ پنل مدرس و آمار دوره‌هایی که به خودش منتسب شده‌اند. مدرس به داشبورد مدیر دسترسی ندارد.

### مدیر

مشاهده داشبورد فروش، مدیریت کاربران و نقش‌ها، فعال/غیرفعال‌کردن کاربران و دوره‌ها، بررسی پیام‌ها، مدیریت کامل داده‌ها از Django Admin و دسترسی به گزارش‌های کل سامانه.

ثبت‌نام عمومی همیشه نقش `STUDENT` می‌سازد. نقش مدرس یا مدیر فقط توسط مدیر تغییر می‌کند.

## چرا Session Authentication؟

این پروژه یک وب‌سایت یکپارچه است که Frontend و Backend روی همان دامنه اجرا می‌شوند. Session Authentication در این سناریو ساده، قابل‌فهم و مناسب ارائه دانشگاهی است. شناسه نشست داخل Cookie قرار می‌گیرد و درخواست‌های تغییردهنده داده با CSRF Token محافظت می‌شوند.

## مهم‌ترین Joinها

- `CartItem -> Cart -> User`: پیدا کردن سبد یک کاربر
- `CartItem -> Course`: نمایش عنوان و قیمت زنده در سبد
- `Order -> User`: سفارش‌های یک مشتری
- `OrderItem -> Order -> User`: جزئیات خرید مشتری
- `OrderItem -> Course`: گزارش فروش هر دوره
- `Enrollment -> User + Course + OrderItem`: اثبات اینکه دسترسی دوره از کدام خرید صادر شده است
- `Course -> Category`: فیلتر دوره‌ها بر اساس دسته‌بندی
- `Course -> Instructor(User)`: نمایش دوره‌های هر مدرس
- `Review -> User + Course`: نظر دانشجو برای یک دوره

توضیح کامل ERD، نوع ارتباط‌ها و دلیل انتخاب هر Foreign Key در [`docs/ARCHITECTURE_FA.md`](docs/ARCHITECTURE_FA.md) آمده است.

## کنترل کیفیت و اجرای تست‌ها

کنترل‌های ساختاری بدون نیاز به نصب Django:

```bash
python scripts/preflight.py
```

پس از نصب وابستگی‌ها:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

تست‌ها جریان‌های مهم زیر را پوشش می‌دهند:

- ثبت‌نام عمومی و اجبار نقش دانشجو
- جلوگیری از ایمیل تکراری
- تفاوت `401` و `403`
- جلوگیری از دوره تکراری در سبد
- Snapshot قیمت سفارش
- پرداخت آزمایشی و ایجاد Enrollment
- جلوگیری از خرید دوباره
- ممنوع بودن ثبت نظر برای غیرخریدار

## ساخت مدیر جدید

علاوه بر حساب نمایشی، می‌توان مدیر جدید ساخت:

```bash
python manage.py createsuperuser
```

## تنظیمات اختیاری محیط

مقادیر پیش‌فرض برای اجرای محلی کافی‌اند. برای ساخت فایل تنظیمات محلی، نمونه را کپی کنید؛ `settings.py` فایل `.env` را بدون وابستگی اضافه می‌خواند و متغیرهای واقعی سیستم همچنان اولویت دارند:

```bash
cp .env.example .env
```

متغیرهای اصلی:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
```

## نکات مهم برای ارائه

1. ابتدا با دانشجو وارد شوید و تلاش کنید `/dashboard/` را باز کنید تا پاسخ واقعی 403 دیده شود.
2. یک دوره به سبد اضافه کنید؛ افزودن دوباره باید با خطای 409 رد شود.
3. Checkout را تکمیل کنید و کد پیگیری پرداخت را نشان دهید.
4. جدول‌های `Order`, `OrderItem`, `Payment` و `Enrollment` را در Django Admin نمایش دهید.
5. قیمت یک دوره را بعد از خرید تغییر دهید و نشان دهید قیمت `OrderItem` قبلی ثابت مانده است.
6. Swagger را باز کنید و جداسازی Routerهای Auth، Catalog، Store، Core و Admin را توضیح دهید.

راهنمای آمادهٔ دفاع و پرسش‌های احتمالی استاد در [`docs/PRESENTATION_GUIDE_FA.md`](docs/PRESENTATION_GUIDE_FA.md) قرار دارد.

## گزارش بررسی و QA

- [گزارش بررسی فرانت اولیه](docs/FRONTEND_REVIEW_FA.md)
- [معماری، ERD و Joinها](docs/ARCHITECTURE_FA.md)
- [Routeها و Endpointها](docs/ROUTES_FA.md)
- [راهنمای دفاع دانشگاهی](docs/PRESENTATION_GUIDE_FA.md)
- [گزارش کنترل کیفیت](docs/QA_REPORT_FA.md)
