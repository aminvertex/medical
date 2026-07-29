# راهنمای ارائه و دفاع پروژه

## سناریوی پیشنهادی ارائه

1. صفحه اصلی و فروشگاه را باز کنید و توضیح دهید داده‌ها از SQLite می‌آیند، نه JavaScript هاردکد.
2. با حساب دانشجو وارد شوید.
3. آدرس `/dashboard/` را باز کنید و پاسخ 403 را نشان دهید.
4. یک دوره به سبد اضافه کنید و دوباره همان دوره را اضافه کنید؛ خطای 409 نشان‌دهنده جلوگیری از Conflict است.
5. وارد Checkout شوید، کد `AI20` را وارد کنید و پرداخت آزمایشی انجام دهید.
6. صفحه موفقیت، کد پیگیری و «دوره‌های من» را نشان دهید.
7. با مدیر وارد شوید و Dashboard، Users، Orders و Django Admin را نمایش دهید.
8. Swagger را باز کنید و Routerها را توضیح دهید.
9. در Django Admin، Join بین Order، OrderItem، Payment و Enrollment را نمایش دهید.

## سؤال‌های احتمالی استاد

### چرا SQLite؟

برای پروژه تک‌سیستمی دانشگاهی نصب جداگانه نمی‌خواهد، فایل دیتابیس قابل حمل است و Django ORM اجازه می‌دهد بعداً با تغییر تنظیمات به PostgreSQL مهاجرت شود.

### چرا Django Ninja؟

Router و Schemaهای تایپ‌شده، مستندات OpenAPI/Swagger و ساخت APIهای تمیز را با کد کم فراهم می‌کند؛ در کنار Templateهای Django برای این پروژه مناسب است.

### رمز کجا ذخیره می‌شود؟

رمز خام ذخیره نمی‌شود. `set_password` آن را با Password Hasher جنگو Hash می‌کند و `check_password/authenticate` برای بررسی استفاده می‌شوند.

### Session چگونه کار می‌کند؟

پس از Login، شناسه Session در Cookie مرورگر قرار می‌گیرد و اطلاعات Session سمت سرور نگهداری می‌شود. درخواست‌های بعدی کاربر را از طریق Cookie می‌شناسند.

### فرق 401 و 403 چیست؟

- 401: کاربر اصلاً احراز هویت نشده است.
- 403: کاربر وارد شده ولی Role لازم را ندارد.

### چرا فقط مخفی‌کردن دکمه مدیریت کافی نیست؟

کاربر می‌تواند URL یا API را مستقیم صدا بزند. بنابراین Permission در Backend کنترل می‌شود؛ مخفی‌کردن لینک فقط بهبود رابط کاربری است.

### چرا OrderItem قیمت را دوباره نگه می‌دارد؟

Course قیمت فعلی را نگه می‌دارد، ولی فاکتور باید قیمت زمان خرید را حفظ کند. به همین دلیل OrderItem یک Snapshot مالی دارد.

### چرا CartItem جدول جدا دارد؟

Cart و Course رابطه Many-to-Many دارند. جدول واسط علاوه بر دو Foreign Key، زمان افزودن و Constraint عدم تکرار را نگه می‌دارد.

### چرا Enrollment جدا از OrderItem است؟

OrderItem سابقه مالی است؛ Enrollment وضعیت دسترسی آموزشی و پیشرفت را نگه می‌دارد. ممکن است در آینده سفارش Refund شود یا دسترسی غیرفعال گردد، بدون اینکه تاریخچه مالی حذف شود.

### Join دقیق گزارش فروش چیست؟

```text
Course -> OrderItem -> Order
```

فقط Orderهایی که `status=PAID` دارند در درآمد محاسبه می‌شوند.

### چطور از تغییر قیمت در مرورگر جلوگیری شده؟

Frontend مبلغ را برای نمایش نشان می‌دهد، اما Backend هنگام Checkout CartItemها را از دیتابیس می‌خواند و Price را از Course محاسبه می‌کند. مبلغ ارسال‌شده از مرورگر پذیرفته نمی‌شود.

### چطور خرید تکراری کنترل می‌شود؟

سه لایه وجود دارد:

1. بررسی Enrollment فعال در Service
2. UniqueConstraint روی CartItem برای سبد تکراری
3. UniqueConstraint روی `(user, course)` در Enrollment

### چرا `transaction.atomic` استفاده شده؟

ساخت Order، OrderItem، Payment، CouponUsage و پاک‌کردن سبد باید یک عملیات واحد باشد. اگر وسط کار خطا رخ دهد، همه تغییرها Rollback می‌شوند.

### `select_related` و `prefetch_related` چه فرقی دارند؟

`select_related` برای ارتباط تک‌ردیفی مانند ForeignKey با JOIN SQL مناسب است. `prefetch_related` برای ارتباط چندردیفی مانند Order Items Query جدا می‌زند و نتیجه را ترکیب می‌کند تا مشکل N+1 کاهش یابد.

## نمایش جدول‌ها در ارائه

پیشنهاد می‌شود این زنجیره را باز کنید:

```text
accounts_user
    -> orders_order
        -> orders_orderitem
            -> orders_enrollment
        -> orders_payment
```

سپس یک Course را باز کنید و ارتباط آن با Category، Instructor، Sections، Reviews و OrderItems را توضیح دهید.
