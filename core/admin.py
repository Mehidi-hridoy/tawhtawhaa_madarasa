from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# ==================== INLINE ADMIN CLASSES ====================

class CourseInstructorInline(admin.TabularInline):
    model = CourseInstructor
    extra = 1

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0

# ==================== MODEL ADMIN CLASSES ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ['name']}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price_type', 
        'simple_price_display', 'is_active'
    ]
    
    list_filter = ['is_active', 'price_type', 'category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ['name']}
    
    inlines = [CourseInstructorInline, ModuleInline]
    
    def simple_price_display(self, obj):
        """Simple price display that won't cause errors"""
        if obj.price_type == 'free':
            return "FREE"
        elif obj.sale_price:
            return f"৳{obj.sale_price}"
        else:
            return f"৳{obj.base_price}"
    simple_price_display.short_description = 'Price'

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'is_published']
    list_filter = ['is_published', 'course']
    search_fields = ['title']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'is_published']
    list_filter = ['lesson_type', 'is_published']
    search_fields = ['title']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'quiz_type', 'is_published']
    list_filter = ['quiz_type', 'is_published']
    search_fields = ['title']

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['short_question', 'quiz', 'question_type']
    list_filter = ['question_type']
    search_fields = ['question_text']
    
    def short_question(self, obj):
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    short_question.short_description = 'Question'

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'role', 'is_active']
    search_fields = ['full_name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'is_active']
    search_fields = ['full_name']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrollment_status']
    list_filter = ['enrollment_status']
    search_fields = ['student__full_name', 'course__name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'student', 'amount', 'status']
    list_filter = ['status']
    search_fields = ['transaction_id']

# ==================== REGISTER OTHER MODELS ====================

admin.site.register(CourseReview)
admin.site.register(Coupon)
admin.site.register(Certificate)
admin.site.register(BlogPost)
admin.site.register(CourseInstructor)
admin.site.register(CourseResource)
admin.site.register(StudentCourseProgress)
admin.site.register(StudentLessonProgress)
admin.site.register(StudentQuizAttempt)
admin.site.register(QuizResponse)
admin.site.register(Notification)
admin.site.register(Gallery)
admin.site.register(Donation)
admin.site.register(FAQ)
admin.site.register(ContactMessage)

# ==================== USER ADMIN ====================

class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False

class InstructorInline(admin.StackedInline):
    model = Instructor
    can_delete = False

class CustomUserAdmin(UserAdmin):
    def get_inlines(self, request, obj=None):
        inlines = []
        if obj:
            if hasattr(obj, 'student_profile'):
                inlines.append(StudentInline)
            if hasattr(obj, 'instructor_profile'):
                inlines.append(InstructorInline)
        return inlines

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)