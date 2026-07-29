from django.contrib import admin
from .models import ContactMessage, NewsletterSubscription


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    list_editable = ("status",)
    readonly_fields = ("created_at",)


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("email",)
    list_editable = ("is_active",)
