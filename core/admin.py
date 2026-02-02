from django.contrib import admin
from .models import (
    Course, Instructor, Student, Enrollment, Payment, BlogPost, Gallery,
    Donation, FAQ, Office, Notification, ContactMessage, SelfLearningCourse, Module, Lesson, InteractiveMCQ, StudentLessonProgress
)
# -------------------------------
# Course Admin
# -------------------------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'level', 'base_fee', 'is_active', 'current_enrollment', 'max_students')
    list_filter = ('category', 'level', 'is_active')
    search_fields = ('name', 'description', 'short_description')
    ordering = ('name',)
    readonly_fields = ('current_enrollment',)

# -------------------------------
# Instructor Admin
# -------------------------------
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'title', 'role', 'experience_years', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('full_name', 'specialization', 'qualifications')
    filter_horizontal = ('courses',)  # for ManyToManyField

# -------------------------------
# Student Admin
# -------------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'phone', 'occupation', 'education', 'is_active')
    list_filter = ('gender', 'occupation', 'education', 'is_active')
    search_fields = ('full_name', 'phone', 'email', 'address', 'city', 'country')

# -------------------------------
# Enrollment Admin
# -------------------------------
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_status', 'payment_status', 'enrolled_at', 'start_date', 'expected_end_date')
    list_filter = ('enrollment_status', 'payment_status', 'course')
    search_fields = ('student__full_name', 'course__name')
    ordering = ('-enrolled_at',)

# -------------------------------
# Payment Admin
# -------------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'enrollment', 'amount', 'payment_method', 'is_verified', 'verified_by', 'payment_date')
    list_filter = ('payment_method', 'is_verified')
    search_fields = ('transaction_id', 'enrollment__student__full_name')
    ordering = ('-payment_date',)

# -------------------------------
# BlogPost Admin
# -------------------------------
@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-published_at',)

# -------------------------------
# Gallery Admin
# -------------------------------
@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'uploaded_at', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('title', 'description')
    ordering = ('-uploaded_at',)

# -------------------------------
# Donation Admin
# -------------------------------
@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'amount', 'payment_method', 'is_verified', 'donated_at')
    list_filter = ('is_verified', 'payment_method', 'is_zakat', 'is_sadaqah', 'is_project_specific')
    search_fields = ('donor_name', 'donor_email', 'donor_phone', 'project_name')
    ordering = ('-donated_at',)

# -------------------------------
# FAQ Admin
# -------------------------------
@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'display_order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    ordering = ('display_order',)

# -------------------------------
# Office Admin
# -------------------------------
@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_main_office', 'is_active')
    list_filter = ('is_main_office', 'is_active', 'city')
    search_fields = ('name', 'address', 'city')
    ordering = ('name',)

# -------------------------------
# Notification Admin
# -------------------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent')
    search_fields = ('title', 'message', 'recipient__username')
    ordering = ('-created_at',)

# -------------------------------
# ContactMessage Admin
# -------------------------------
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'status', 'priority', 'is_read', 'received_at')
    list_filter = ('status', 'priority', 'is_read', 'is_important')
    search_fields = ('name', 'email', 'phone', 'subject', 'message')
    ordering = ('-received_at',)


# admin.py
from django.contrib import admin
from .models import SelfLearningCourse, Module, Lesson, InteractiveMCQ, MCQOption

@admin.register(SelfLearningCourse)
class SelfLearningCourseAdmin(admin.ModelAdmin):
    list_display = ['course', 'is_self_paced', 'total_modules', 'total_lessons']
    list_filter = ['is_self_paced', 'certificate_available']
    search_fields = ['course__name']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'self_learning_course', 'order', 'duration_minutes', 'is_active']
    list_filter = ['is_active', 'self_learning_course']
    ordering = ['self_learning_course', 'order']
    search_fields = ['title', 'description']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'order', 'duration_minutes', 'is_required']
    list_filter = ['lesson_type', 'is_required', 'module']
    ordering = ['module', 'order']
    search_fields = ['title', 'description']
    filter_horizontal = ['prerequisite_lessons']

class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 4

@admin.register(InteractiveMCQ)
class InteractiveMCQAdmin(admin.ModelAdmin):
    list_display = ['question', 'lesson', 'appear_at_second', 'question_type', 'is_required']
    list_filter = ['question_type', 'is_required', 'lesson']
    search_fields = ['question']
    inlines = [MCQOptionInline]

@admin.register(StudentLessonProgress)
class StudentLessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'status', 'video_progress_seconds', 'points_earned']
    list_filter = ['status', 'lesson__module__self_learning_course__course']
    search_fields = ['student__full_name', 'lesson__title']