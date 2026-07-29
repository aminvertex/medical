# Routeها و Endpointهای پروژه

## مسیرهای صفحه‌ای Django

| Method | Route | دسترسی | کاربرد |
|---|---|---|---|
| GET | `/` | عمومی | خانه و دوره‌های منتخب |
| GET | `/shop/` | عمومی | فروشگاه، جست‌وجو و فیلتر |
| GET | `/courses/<slug>/` | عمومی | جزئیات دوره |
| GET | `/auth/` | عمومی | ورود و ثبت‌نام |
| POST | `/logout/` | واردشده | خروج با CSRF |
| GET | `/cart/` | واردشده | سبد خرید |
| GET | `/checkout/` | واردشده | فرم Checkout |
| GET | `/checkout/success/<number>/` | مالک سفارش/مدیر | نتیجه پرداخت |
| GET | `/account/` | واردشده | خلاصه حساب |
| GET | `/account/orders/` | واردشده | سفارش‌های خود کاربر |
| GET | `/account/courses/` | واردشده | دوره‌های فعال خود کاربر |
| GET | `/account/favorites/` | واردشده | علاقه‌مندی‌ها |
| GET | `/dashboard/` | مدیر | داشبورد مدیریتی |
| GET | `/dashboard/users/` | مدیر | مدیریت کاربران |
| GET | `/dashboard/courses/` | مدیر | وضعیت دوره‌ها |
| GET | `/dashboard/orders/` | مدیر | فروش و سفارش‌ها |
| GET | `/dashboard/messages/` | مدیر | پیام‌های تماس |
| GET | `/instructor/` | مدرس/مدیر | آمار دوره‌های مدرس |
| GET | `/django-admin/` | Staff مجاز | پنل استاندارد Django |
| GET | `/api/docs` | عمومی محلی | Swagger |

## API احراز هویت — `/api/v1/auth`

| Method | Endpoint | Auth | نتیجه |
|---|---|---|---|
| POST | `/register` | عمومی + CSRF | ساخت Student و ورود خودکار |
| POST | `/login` | عمومی + CSRF | ایجاد Session |
| POST | `/logout` | Session | حذف Session |
| GET | `/me` | Session | اطلاعات کاربر جاری |

## API کاتالوگ — `/api/v1/catalog`

| Method | Endpoint | Auth | نتیجه |
|---|---|---|---|
| GET | `/categories` | عمومی | دسته‌ها |
| GET | `/courses` | عمومی | دوره‌ها با فیلتر و Sort |
| GET | `/courses/{slug}` | عمومی | جزئیات و سرفصل‌ها |
| POST | `/courses/{id}/favorite` | دانشجو/مدرس/مدیر | Toggle علاقه‌مندی |
| POST | `/courses/{id}/reviews` | خریدار واردشده | ثبت نظر Pending |

## API فروشگاه — `/api/v1/store`

| Method | Endpoint | Auth | نتیجه |
|---|---|---|---|
| GET | `/cart` | Session | سبد کاربر جاری |
| POST | `/cart/items` | Session | افزودن یک Course ID |
| DELETE | `/cart/items/{course_id}` | Session | حذف از سبد |
| POST | `/checkout` | Session | ساخت Order از قیمت سرور |
| POST | `/orders/{number}/pay` | مالک/مدیر | پرداخت شبیه‌سازی‌شده |
| GET | `/orders` | Session | سفارش‌های کاربر جاری |

## API محتوای عمومی — `/api/v1/core`

| Method | Endpoint | Auth | نتیجه |
|---|---|---|---|
| POST | `/contact` | عمومی + CSRF | ذخیره پیام تماس |
| POST | `/newsletter` | عمومی + CSRF | عضویت/فعال‌سازی خبرنامه |

## API مدیریت — `/api/v1/admin`

تمام Endpointهای این Router با `admin_auth` محافظت می‌شوند. کاربر Anonymous پاسخ 401 و کاربر واردشده با نقش اشتباه پاسخ 403 می‌گیرد.

| Method | Endpoint | نتیجه |
|---|---|---|
| GET | `/stats` | KPIهای کاربران، فروش و پیام‌ها |
| GET | `/users` | فهرست و جست‌وجوی کاربران |
| PATCH | `/users/{id}` | تغییر Role یا Active |
| PATCH | `/courses/{id}/status` | انتشار/غیرفعال‌سازی دوره |
| PATCH | `/messages/{id}` | تغییر وضعیت پیام |

## دلیل جداسازی Routerها

- `auth`: هویت و Session
- `catalog`: داده‌های قابل مشاهده فروشگاه
- `store`: تراکنش‌های خرید
- `core`: فرم‌های عمومی
- `admin`: عملیات حساس مدیریتی

این جداسازی خوانایی URLها، مستندسازی Swagger، تست و اعمال Permission را ساده می‌کند.
