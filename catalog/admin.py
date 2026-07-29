from django.contrib import admin
from .models import Category, Course, CourseSection, Favorite, Lesson, Review


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 1
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "category", "instructor", "price", "level", "is_active", "is_featured", "is_bestseller")
    list_filter = ("is_active", "is_featured", "is_bestseller", "level", "category")
    search_fields = ("code", "title", "short_description", "instructor__email")
    list_editable = ("is_active", "is_featured", "is_bestseller")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [CourseSectionInline]


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "order")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "rating", "status", "created_at")
    list_filter = ("status", "rating", "created_at")
    search_fields = ("user__email", "course__title", "comment")
    list_editable = ("status",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "created_at")
    search_fields = ("user__email", "course__title")
