from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Course, CourseInstructor, Instructor,
    Student, Module, Lesson, Quiz, QuizQuestion,
    Enrollment, StudentCourseProgress, StudentLessonProgress,
    StudentQuizAttempt, QuizResponse, Payment, Certificate,
    CourseResource, CourseReview, Coupon, Notification,
    BlogPost, Gallery, Donation, FAQ, ContactMessage
)


# =====================
# Inline Classes
# =====================

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ('order', 'title', 'duration_minutes', 'is_published')
    show_change_link = True
    ordering = ('order',)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'lesson_type', 'duration_minutes', 'is_published', 'is_free', 'points_value')
    show_change_link = True
    ordering = ('order',)


class QuizInline(admin.StackedInline):  # Using StackedInline for better visibility of quiz details
    model = Quiz
    extra = 0  # Since OneToOne, no extras
    fields = ('title', 'quiz_type', 'duration_minutes', 'passing_score', 'max_attempts', 'is_published')
    show_change_link = True


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ('order', 'question_text', 'question_type', 'points', 'is_active')
    show_change_link = True
    ordering = ('order',)


class CourseResourceInline(admin.TabularInline):
    model = CourseResource
    extra = 0
    fields = ('title', 'resource_type', 'is_free', 'is_active')


class CourseInstructorInline(admin.TabularInline):
    model = CourseInstructor
    extra = 1
    fields = ('instructor', 'display_order')
    raw_id_fields = ('instructor',)


# =====================
# ModelAdmin Classes
# =====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'display_order', 'is_active', 'get_active_courses_count')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('display_order', 'is_active')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'course_type', 'level', 'price_type',
        'get_current_price', 'is_active', 'is_featured', 'is_approved',
        'total_enrollments', 'created_by', 'created_at'
    )
    list_filter = (
        'course_type', 'level', 'price_type', 'is_active',
        'is_featured', 'is_approved', 'category'
    )
    search_fields = ('name', 'short_description', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [
        CourseInstructorInline,
        ModuleInline,
        CourseResourceInline,
    ]
    readonly_fields = ('average_rating', 'review_count', 'total_enrollments', 'total_completions',
                       'created_at', 'updated_at', 'get_current_price', 'get_discount_percentage')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'course_type', 'level')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'learning_outcomes')
        }),
        ('Pricing', {
            'fields': ('price_type', 'base_price', 'sale_price', 'currency')
        }),
        ('Media', {
            'fields': ('thumbnail', 'featured_image', 'promo_video_url')
        }),
        ('Settings & Status', {
            'fields': ('is_active', 'is_featured', 'is_approved', 'certificate_available',
                       'requires_completion_certificate')
        }),
        ('Statistics (readonly)', {
            'fields': ('total_enrollments', 'total_completions', 'average_rating', 'review_count'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'experience_years', 'is_active', 'total_courses', 'total_students')
    list_filter = ('role', 'is_active')
    search_fields = ('full_name', 'bio', 'specialization', 'user__username', 'user__email')
    readonly_fields = ('total_courses', 'total_students', 'created_at', 'updated_at')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'gender', 'occupation', 'country', 'total_courses_enrolled', 'total_points')
    list_filter = ('gender', 'occupation', 'country', 'is_active', 'email_verified')
    search_fields = ('full_name', 'user__username', 'user__email', 'phone')
    readonly_fields = ('total_courses_enrolled', 'total_courses_completed', 'total_points',
                       'registration_date', 'last_active')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'duration_minutes', 'is_published', 'get_total_lessons')
    list_filter = ('is_published',)
    search_fields = ('title', 'description', 'course__name')
    raw_id_fields = ('course',)
    inlines = [LessonInline]  # Lessons under modules


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_module', 'get_course', 'lesson_type', 'order', 'duration_minutes', 'is_free', 'is_published')
    list_filter = ('lesson_type', 'is_free', 'is_published', 'module__course')
    search_fields = ('title', 'description', 'module__title', 'module__course__name')
    raw_id_fields = ('module',)
    inlines = [QuizInline]  # Quiz (MCQs) under lessons

    def get_module(self, obj):
        return obj.module.title if obj.module else '-'
    get_module.short_description = 'Module'

    def get_course(self, obj):
        return obj.module.course.name if obj.module and obj.module.course else '-'
    get_course.short_description = 'Course'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'get_lesson', 'get_module', 'get_course', 'quiz_type', 'duration_minutes', 'passing_score', 'is_published')
    list_filter = ('quiz_type', 'is_published')
    search_fields = ('title', 'description', 'course__name', 'module__title', 'lesson__title')
    inlines = [QuizQuestionInline]  # MCQs (questions) under quizzes

    def get_lesson(self, obj):
        return obj.lesson.title if obj.lesson else '-'
    get_lesson.short_description = 'Lesson'

    def get_module(self, obj):
        if obj.module:
            return obj.module.title
        elif obj.lesson and obj.lesson.module:
            return obj.lesson.module.title
        return '-'
    get_module.short_description = 'Module'

    def get_course(self, obj):
        if obj.course:
            return obj.course.name
        elif obj.module and obj.module.course:
            return obj.module.course.name
        elif obj.lesson and obj.lesson.module and obj.lesson.module.course:
            return obj.lesson.module.course.name
        return '-'
    get_course.short_description = 'Course'


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'get_quiz', 'get_lesson', 'get_module', 'get_course', 'question_type', 'points', 'order', 'is_active')
    list_filter = ('question_type', 'is_active', 'quiz__quiz_type')
    search_fields = ('question_text', 'quiz__title')

    def get_quiz(self, obj):
        return obj.quiz.title if obj.quiz else '-'
    get_quiz.short_description = 'Quiz'

    def get_lesson(self, obj):
        return obj.quiz.get_lesson() if obj.quiz else '-'
    get_lesson.short_description = 'Lesson'

    def get_module(self, obj):
        return obj.quiz.get_module() if obj.quiz else '-'
    get_module.short_description = 'Module'

    def get_course(self, obj):
        return obj.quiz.get_course() if obj.quiz else '-'
    get_course.short_description = 'Course'


# ... Register other models with sensible defaults ...

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_status', 'payment_status', 'progress_percentage', 'enrolled_at')
    list_filter = ('enrollment_status', 'payment_status', 'course')
    search_fields = ('student__full_name', 'course__name')
    readonly_fields = ('progress_percentage', 'total_time_spent', 'completed_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'student', 'enrollment', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('payment_method', 'status', 'is_verified')
    search_fields = ('transaction_id', 'student__full_name', 'enrollment__course__name')
    readonly_fields = ('payment_date', 'verified_at', 'gateway_response')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'course', 'issued_date', 'grade')
    list_filter = ('course',)
    search_fields = ('certificate_id', 'student__full_name', 'course__name')


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'course')
    search_fields = ('student__full_name', 'course__name', 'title')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'used_count', 'usage_limit', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'status', 'priority', 'received_at', 'is_read')
    list_filter = ('status', 'priority', 'subject_type')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('received_at', 'read_at', 'resolved_at')


# Register remaining models with basic sensible configuration
admin.site.register([
    StudentCourseProgress, StudentLessonProgress, StudentQuizAttempt, QuizResponse,
    CourseResource, Notification, BlogPost, Gallery, Donation, FAQ
])