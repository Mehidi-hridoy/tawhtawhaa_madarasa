
# ==================== SIGNALS ====================
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from models import Enrollment, StudentLessonProgress, Payment


@receiver(post_save, sender=Enrollment)
def update_course_enrollment_count(sender, instance, created, **kwargs):
    """Update course enrollment count when enrollment is created/deleted"""
    if created:
        instance.course.enrollment_count += 1
        instance.course.save()

@receiver(post_delete, sender=Enrollment)
def decrease_course_enrollment_count(sender, instance, **kwargs):
    """Decrease course enrollment count when enrollment is deleted"""
    instance.course.enrollment_count = max(0, instance.course.enrollment_count - 1)
    instance.course.save()

@receiver(post_save, sender=StudentLessonProgress)
def update_enrollment_progress(sender, instance, **kwargs):
    """Update enrollment progress when lesson progress changes"""
    if instance.enrollment and instance.status == 'completed':
        instance.enrollment.update_progress()

@receiver(post_save, sender=Payment)
def activate_enrollment_on_payment(sender, instance, created, **kwargs):
    """Activate enrollment when payment is verified"""
    if instance.is_verified and instance.enrollment.enrollment_status == 'pending':
        instance.enrollment.enrollment_status = 'active'
        instance.enrollment.start_date = timezone.now().date()
        instance.enrollment.save()

