from django.contrib import admin
from .models import Cart, CartItem, Coupon, CouponUsage, Enrollment, Order, OrderItem, Payment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("added_at",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__email",)
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("course", "course_code", "course_title", "unit_price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "subtotal", "discount_amount", "total_amount", "created_at", "paid_at")
    list_filter = ("status", "created_at", "paid_at")
    search_fields = ("number", "user__email", "customer_phone")
    readonly_fields = ("number", "subtotal", "discount_amount", "total_amount", "created_at", "paid_at", "updated_at")
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "status", "reference_code", "gateway", "paid_at")
    list_filter = ("status", "gateway")
    search_fields = ("order__number", "reference_code")
    readonly_fields = ("created_at",)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "discount_percent", "starts_at", "ends_at", "is_active")
    list_filter = ("is_active", "starts_at", "ends_at")
    search_fields = ("code", "title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "is_active", "progress_percent", "enrolled_at")
    list_filter = ("is_active", "enrolled_at")
    search_fields = ("user__email", "course__title", "course__code")

admin.site.register(CouponUsage)
