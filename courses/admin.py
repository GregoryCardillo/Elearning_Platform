from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Course, Module, Lesson

# Register your models here.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model.
    """
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role', 'bio', 'profile_picture' )}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')})
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )

from .models import User, Course, Module, Lesson


# ... UserAdmin code già esistente ...


class ModuleInline(admin.TabularInline):
    """
    Inline admin to manage modules directly from course page.
    """
    model = Module
    extra = 1
    fields = ('title', 'order', 'description')


class LessonInline(admin.TabularInline):
    """
    Inline admin to manage lessons directly from module page.
    """
    model = Lesson
    extra = 1
    fields = ('title', 'content_type', 'order', 'duration_minutes', 'is_free')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'level', 'status', 'price', 'created_at')
    list_filter = ('level', 'status', 'created_at')
    search_fields = ('title', 'description', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ModuleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'instructor', 'thumbnail')
        }),
        ('Course Details', {
            'fields': ('level', 'status', 'price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize query with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('instructor')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'total_lessons', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LessonInline]
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'duration_minutes', 'order', 'is_free')
    list_filter = ('content_type', 'is_free', 'created_at')
    search_fields = ('title', 'content', 'module__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'content_type', 'order')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'attachments', 'duration_minutes', 'is_free')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )