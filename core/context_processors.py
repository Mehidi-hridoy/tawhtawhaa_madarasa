# core/context_processors.py
from .models import Category
from django.db.models import Count, Q

def navbar_context(request):
    """Context processor for navbar data"""
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True, courses__is_approved=True))
    ).filter(course_count__gt=0).order_by('-display_order', 'name')[:8]
    
    # User-specific stats for authenticated users
    enrolled_courses_count = 0
    completed_lessons = 0
    certificates_count = 0
    
    if request.user.is_authenticated:
        try:
            from .models import Enrollment, StudentLessonProgress, Certificate
            
            # Get student's enrolled courses count
            student = request.user.student_profile
            enrolled_courses_count = Enrollment.objects.filter(
                student=student,
                enrollment_status='active'
            ).count()
            
            # Get completed lessons count
            completed_lessons = StudentLessonProgress.objects.filter(
                student=student,
                status='completed'
            ).count()
            
            # Get certificates count
            certificates_count = Certificate.objects.filter(
                student=student
            ).count()
            
        except Exception:
            pass
    
    return {
        'categories': categories,
        'enrolled_courses_count': enrolled_courses_count,
        'completed_lessons': completed_lessons,
        'certificates_count': certificates_count,
    }