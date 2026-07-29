from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password

from .models import InstructorProfile, User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="رمز عبور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تکرار رمز عبور", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "role")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("رمزها یکسان نیستند.")
        if p2:
            candidate = self.instance
            candidate.email = self.cleaned_data.get("email", "")
            candidate.first_name = self.cleaned_data.get("first_name", "")
            candidate.last_name = self.cleaned_data.get("last_name", "")
            validate_password(p2, user=candidate)
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="رمز عبور")

    class Meta:
        model = User
        fields = "__all__"

    def clean_password(self):
        # مقدار Hash هنگام ویرایش کاربر تغییر نمی‌کند؛ تغییر رمز از فرم مخصوص انجام می‌شود.
        return self.initial.get("password")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("email", "full_name", "phone", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("اطلاعات شخصی", {"fields": ("first_name", "last_name", "phone", "role")}),
        ("دسترسی", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("زمان‌ها", {"fields": ("last_login", "date_joined", "updated_at")}),
    )
    readonly_fields = ("date_joined", "updated_at", "last_login")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "first_name", "last_name", "phone", "role", "password1", "password2")}),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "expertise", "is_featured")
    list_filter = ("is_featured",)
    search_fields = ("user__email", "user__first_name", "user__last_name", "expertise")
