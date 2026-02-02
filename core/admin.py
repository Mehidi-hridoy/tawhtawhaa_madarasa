from django.contrib import admin
from .models import (
    Category, Coupon, Course, Lesson, Module, Student, 
    CourseInstructor, CourseResource, Enrollment, Wishlist, 
    Notification, FAQ, ContactMessage, BlogPost, Quiz, 
    QuizQuestion, QuizResponse, StudentQuizAttempt
)

# Basic admin registration
admin.site.register(Category)
admin.site.register(Coupon)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Module)
admin.site.register(Student)
admin.site.register(CourseInstructor)
admin.site.register(CourseResource)
admin.site.register(Enrollment)
admin.site.register(Wishlist)
admin.site.register(Notification)
admin.site.register(FAQ)
admin.site.register(ContactMessage)
admin.site.register(BlogPost)
admin.site.register(Quiz)
admin.site.register(QuizQuestion)
admin.site.register(QuizResponse)
admin.site.register(StudentQuizAttempt)
