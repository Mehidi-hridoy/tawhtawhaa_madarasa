# core/templatetags/custom_filters.py
from django import template
from ..models import Enrollment

register = template.Library()

@register.filter
def is_enrolled_in(student, course):
    """Check if student is enrolled in a course"""
    if student and course:
        return Enrollment.objects.filter(
            student=student,
            course=course,
            enrollment_status='active'
        ).exists()
    return False

@register.filter
def has_completed_course(student, course):
    """Check if student has completed a course"""
    if student and course:
        return Enrollment.objects.filter(
            student=student,
            course=course,
            enrollment_status='completed'
        ).exists()
    return False


@register.filter
def split(value, arg):
    """Split a string by the given argument"""
    return value.split(arg) if value else []