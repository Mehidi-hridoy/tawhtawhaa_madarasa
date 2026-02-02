from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
import json
from .models import *
from .forms import *
from django.contrib.auth.decorators import user_passes_test
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserUpdateForm, StudentUpdateForm, StudentRegistrationForm

# Home Page View
def home(request):
    """Home page view with featured courses and stats"""
    featured_courses = Course.objects.filter(is_active=True, current_enrollment__lt=F('max_students')).order_by('-created_at')[:6]
    featured_instructors = Instructor.objects.filter(is_active=True).order_by('display_order')[:4]
    recent_posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')[:3]
    
    # Statistics
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'active_courses': Course.objects.filter(is_active=True).count(),
        'total_enrollments': Enrollment.objects.count(),
        'successful_completions': Enrollment.objects.filter(enrollment_status='completed').count(),
    }
    
    context = {
        'featured_courses': featured_courses,
        'featured_instructors': featured_instructors,
        'recent_posts': recent_posts,
        'stats': stats,
        'title': 'Home - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'core/home.html', context)

# Courses Views
def courses(request):
    """Display all available courses"""
    category = request.GET.get('category', '')
    level = request.GET.get('level', '')
    
    courses_qs = Course.objects.filter(is_active=True)
    
    if category:
        courses_qs = courses_qs.filter(category=category)
    if level:
        courses_qs = courses_qs.filter(level=level)
    
    # Pagination
    paginator = Paginator(courses_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'courses': page_obj,
        'categories': Course.COURSE_CATEGORIES,
        'levels': Course.LEVEL_CHOICES,
        'selected_category': category,
        'selected_level': level,
        'title': 'Our Courses - Zin Nurain Online Madarasa',
    }
    return render(request, 'courses/course_list.html', context)



def course_detail(request, course_id):
    """Display course details"""
    course = get_object_or_404(Course, id=course_id, is_active=True)

    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True
    ).exclude(id=course.id)[:3]

    enrollment = None
    is_enrolled = False
    is_pending = False
    is_active = False

    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        enrollment = Enrollment.objects.filter(
            student=request.user.student_profile,
            course=course
        ).first()

        if enrollment:
            is_enrolled = True
            if enrollment.enrollment_status == 'pending':
                is_pending = True
            elif enrollment.enrollment_status in ['active', 'completed']:
                is_active = True

    context = {
        'course': course,
        'related_courses': related_courses,
        'is_enrolled': is_enrolled,
        'is_pending': is_pending,
        'is_active': is_active,
        'title': f'{course.name} - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, course_id):
    """Enroll in a course using student profile data"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    student = getattr(request.user, 'student_profile', None)
    
    # Check if student profile exists
    if not student:
        messages.error(request, 'Please complete your student profile first before enrolling in courses.')
        return redirect('core:profile_settings')
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        enrollment_status__in=['active', 'pending']
    ).first()
    
    if existing_enrollment:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('core:course_detail', course_id=course_id)
    
    # Check course availability
    if course.current_enrollment >= course.max_students:
        messages.error(request, 'This course is currently full. Please try another course or check back later.')
        return redirect('core:course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.course = course
            enrollment.course_fee = course.base_fee
            enrollment.due_amount = course.base_fee
            
            # Set start date (next Monday)
            from datetime import date, timedelta
            today = date.today()
            days_until_monday = (0 - today.weekday()) % 7  # Monday = 0
            next_monday = today + timedelta(days=days_until_monday)
            enrollment.start_date = next_monday
            
            # Calculate expected end date
            expected_end_date = next_monday + timedelta(weeks=course.duration_weeks)
            enrollment.expected_end_date = expected_end_date
            
            # Apply discount if available
            if course.discount_fee:
                enrollment.course_fee = course.discount_fee
                enrollment.discount_applied = course.base_fee - course.discount_fee
                enrollment.due_amount = course.discount_fee
            
            # Set default values from student profile
            enrollment.assigned_instructor = course.instructors.first() if course.instructors.exists() else None
            enrollment.preferred_language = student.preferred_language
            
            # Set payment status
            enrollment.payment_status = 'pending'
            enrollment.enrollment_status = 'pending'  # Will be active after payment
            
            # Handle installments
            if form.cleaned_data.get('is_installment'):
                enrollment.is_installment = True
                enrollment.installment_count = form.cleaned_data.get('installment_count', 1)
                
                # Calculate installment amount
                if enrollment.installment_count > 1:
                    installment_amount = enrollment.due_amount / enrollment.installment_count
                    # Round to 2 decimal places
                    installment_amount = round(installment_amount, 2)
                    
                    # Set next installment date (30 days from now)
                    enrollment.next_installment_date = today + timedelta(days=30)
            else:
                enrollment.is_installment = False
                enrollment.installment_count = 1
            
            enrollment.save()
            
            # Update course enrollment count
            course.current_enrollment += 1
            course.save()
            
            # Send enrollment confirmation email (optional)
            try:
                from django.core.mail import send_mail
                send_mail(
                    f'Enrollment Confirmation - {course.name}',
                    f'Dear {student.full_name},\n\n'
                    f'You have successfully enrolled in {course.name}.\n'
                    f'Course Fee: ৳{enrollment.course_fee}\n'
                    f'Payment Status: {enrollment.get_payment_status_display()}\n'
                    f'Please complete your payment to start the course.\n\n'
                    f'Thank you,\nTaw Haa Zin Nurain Online Madarasa',
                    'no-reply@madarasa.com',
                    [request.user.email],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, f'Successfully enrolled in {course.name}! Please complete payment to start classes.')
            return redirect('core:make_payment', enrollment_id=enrollment.id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # GET request - initialize form
        initial_data = {
            'class_time_slot': '',
            'is_installment': False,
            'installment_count': 1,
        }
        form = EnrollmentForm(initial=initial_data)
    
    # Get available time slots
    time_slots = []
    if course.morning_slot:
        time_slots.append(('morning', 'Morning (8:00 AM - 12:00 PM)'))
    if course.afternoon_slot:
        time_slots.append(('afternoon', 'Afternoon (2:00 PM - 6:00 PM)'))
    if course.evening_slot:
        time_slots.append(('evening', 'Evening (6:00 PM - 10:00 PM)'))
    if course.night_slot:
        time_slots.append(('night', 'Night (10:00 PM - 12:00 AM)'))
    
    context = {
        'course': course,
        'form': form,
        'student': student,
        'time_slots': time_slots,
        'title': f'Enroll in {course.name}',
    }
    
    return render(request, 'courses/enroll.html', context)



@login_required
def learning_dashboard(request, course_id):
    """Main learning dashboard for a course"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    try:
        course = Course.objects.get(id=course_id)
        enrollment = Enrollment.objects.get(
            student=request.user.student_profile,
            course=course,
            enrollment_status='active'
        )
    except (Course.DoesNotExist, Enrollment.DoesNotExist):
        messages.error(request, 'Course not found or you are not enrolled.')
        return redirect('dashboard:my_courses')
    
    # Get or create course progress
    course_progress, created = StudentCourseProgress.objects.get_or_create(
        student=request.user.student_profile,
        course=course
    )
    
    # Get modules and lessons
    try:
        self_learning = course.self_learning
        modules = self_learning.modules.all().prefetch_related('lessons')
        
        # Get student progress for each lesson
        for module in modules:
            for lesson in module.lessons.all():
                lesson.progress, _ = StudentLessonProgress.objects.get_or_create(
                    student=request.user.student_profile,
                    lesson=lesson,
                    defaults={'status': 'locked'}
                )
                # Check if lesson should be unlocked
                if lesson.order == 1 and module.order == 1:
                    lesson.progress.status = 'not_started'
                    lesson.progress.save()
                elif lesson.prerequisite_lessons.exists():
                    # Check if all prerequisites are completed
                    prerequisites = lesson.prerequisite_lessons.all()
                    completed_prerequisites = StudentLessonProgress.objects.filter(
                        student=request.user.student_profile,
                        lesson__in=prerequisites,
                        status='completed'
                    ).count()
                    if completed_prerequisites == prerequisites.count():
                        lesson.progress.status = 'not_started'
                        lesson.progress.save()
    
    except Course.self_learning.RelatedObjectDoesNotExist:
        messages.error(request, 'This course is not available for self-learning.')
        return redirect('dashboard:my_courses')
    
    context = {
        'course': course,
        'self_learning': self_learning,
        'modules': modules,
        'course_progress': course_progress,
        'enrollment': enrollment,
        'title': f'Learning - {course.name}',
    }
    
    return render(request, 'learning/dashboard.html', context)

@login_required
def lesson_view(request, course_id, lesson_id):
    """View for individual lesson with interactive video"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    try:
        lesson = Lesson.objects.get(id=lesson_id, module__self_learning_course__course_id=course_id)
        student = request.user.student_profile
        
        # Get or create lesson progress
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'status': 'in_progress', 'started_at': timezone.now()}
        )
        
        if progress.status == 'not_started':
            progress.status = 'in_progress'
            progress.started_at = timezone.now()
            progress.save()
        
        # Update last accessed
        progress.last_accessed = timezone.now()
        progress.save()
        
        # Update course progress current position
        course_progress, _ = StudentCourseProgress.objects.get_or_create(
            student=student,
            course_id=course_id
        )
        course_progress.current_lesson = lesson
        course_progress.current_module = lesson.module
        course_progress.last_accessed = timezone.now()
        course_progress.save()
        
        # Get interactive MCQs for this lesson
        mcqs = InteractiveMCQ.objects.filter(lesson=lesson).prefetch_related('options')
        
        # Prepare MCQs data for JavaScript
        mcqs_data = []
        for mcq in mcqs:
            mcqs_data.append({
                'id': mcq.id,
                'question': mcq.question,
                'type': mcq.question_type,
                'appear_at': mcq.appear_at_second,
                'time_limit': mcq.time_limit_seconds,
                'allow_skip': mcq.allow_skip,
                'max_attempts': mcq.max_attempts,
                'options': [
                    {
                        'id': option.id,
                        'text': option.text,
                        'is_correct': option.is_correct
                    } for option in mcq.options.all()
                ]
            })
        
    except Lesson.DoesNotExist:
        messages.error(request, 'Lesson not found.')
        return redirect('learning:dashboard', course_id=course_id)
    
    context = {
        'lesson': lesson,
        'progress': progress,
        'course': lesson.module.self_learning_course.course,
        'youtube_id': lesson.get_youtube_id(),
        'mcqs_json': json.dumps(mcqs_data),
        'title': f'{lesson.title} - {lesson.module.self_learning_course.course.name}',
    }
    
    return render(request, 'learning/lesson_view.html', context)

@login_required
def submit_mcq_response(request):
    """Handle MCQ responses from video"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        mcq_id = data.get('mcq_id')
        selected_option_ids = data.get('selected_options', [])
        response_time = data.get('response_time', 0)
        video_time = data.get('video_time', 0)
        
        mcq = InteractiveMCQ.objects.get(id=mcq_id)
        student = request.user.student_profile
        
        # Check if student has reached attempt limit
        attempts = StudentMCQResponse.objects.filter(
            student=student,
            mcq=mcq
        ).count()
        
        if attempts >= mcq.max_attempts:
            return JsonResponse({
                'error': 'Maximum attempts reached',
                'max_attempts': mcq.max_attempts
            }, status=400)
        
        # Get selected options
        selected_options = MCQOption.objects.filter(id__in=selected_option_ids)
        
        # Check if answer is correct
        is_correct = True
        correct_options = mcq.options.filter(is_correct=True)
        
        if mcq.question_type == 'single':
            is_correct = selected_options.count() == 1 and selected_options.first().is_correct
        else:  # multiple
            selected_correct = selected_options.filter(is_correct=True).count()
            is_correct = (selected_correct == correct_options.count() and 
                         selected_options.count() == correct_options.count())
        
        # Calculate points earned
        points_earned = mcq.points_value if is_correct else 0
        
        # Save response
        response = StudentMCQResponse.objects.create(
            student=student,
            mcq=mcq,
            is_correct=is_correct,
            response_time_seconds=response_time,
            points_earned=points_earned
        )
        response.selected_options.set(selected_options)
        
        # Update lesson progress
        lesson_progress, _ = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=mcq.lesson
        )
        
        # Update video progress if needed
        if video_time > lesson_progress.video_progress_seconds:
            lesson_progress.video_progress_seconds = video_time
        
        # Add points
        lesson_progress.points_earned += points_earned
        lesson_progress.save()
        
        # Update course points
        course_progress, _ = StudentCourseProgress.objects.get_or_create(
            student=student,
            course=mcq.lesson.module.self_learning_course.course
        )
        course_progress.total_points += points_earned
        course_progress.save()
        
        # Prepare response with explanations
        explanations = []
        for option in mcq.options.all():
            if option.explanation:
                explanations.append({
                    'option_id': option.id,
                    'explanation': option.explanation,
                    'is_correct': option.is_correct
                })
        
        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'points_earned': points_earned,
            'total_points': course_progress.total_points,
            'attempts_made': attempts + 1,
            'max_attempts': mcq.max_attempts,
            'explanations': explanations,
            'correct_options': list(correct_options.values_list('id', flat=True))
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except InteractiveMCQ.DoesNotExist:
        return JsonResponse({'error': 'MCQ not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def complete_lesson(request, lesson_id):
    """Mark lesson as completed"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        student = request.user.student_profile
        
        progress = StudentLessonProgress.objects.get(
            student=student,
            lesson=lesson
        )
        
        # Check if all required MCQs are answered
        required_mcqs = InteractiveMCQ.objects.filter(
            lesson=lesson,
            is_required=True
        )
        
        for mcq in required_mcqs:
            responses = StudentMCQResponse.objects.filter(
                student=student,
                mcq=mcq
            )
            if not responses.exists():
                return JsonResponse({
                    'error': f'Please complete all required questions: {mcq.question[:50]}...'
                }, status=400)
        
        # Mark as completed
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.points_earned += lesson.points_value
        progress.save()
        
        # Update course progress
        course_progress, _ = StudentCourseProgress.objects.get_or_create(
            student=student,
            course=lesson.module.self_learning_course.course
        )
        course_progress.total_points += lesson.points_value
        course_progress.update_progress()
        
        # Check if next lesson should be unlocked
        next_lesson = Lesson.objects.filter(
            module=lesson.module,
            order=lesson.order + 1
        ).first()
        
        if not next_lesson:
            next_lesson = Lesson.objects.filter(
                module__order=lesson.module.order + 1,
                order=1
            ).first()
        
        next_lesson_url = None
        if next_lesson:
            # Unlock next lesson
            next_progress, _ = StudentLessonProgress.objects.get_or_create(
                student=student,
                lesson=next_lesson
            )
            if next_progress.status == 'locked':
                next_progress.status = 'not_started'
                next_progress.save()
            
            next_lesson_url = reverse('learning:lesson_view', kwargs={
                'course_id': lesson.module.self_learning_course.course.id,
                'lesson_id': next_lesson.id
            })
        
        return JsonResponse({
            'success': True,
            'lesson_completed': True,
            'next_lesson_url': next_lesson_url,
            'course_progress': course_progress.overall_progress,
            'total_points': course_progress.total_points
        })
        
    except (Lesson.DoesNotExist, StudentLessonProgress.DoesNotExist):
        return JsonResponse({'error': 'Lesson not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def save_video_progress(request):
    """Save video watch progress"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        progress_seconds = data.get('progress_seconds')
        watch_duration = data.get('watch_duration')
        
        student = request.user.student_profile
        lesson = Lesson.objects.get(id=lesson_id)
        
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=lesson
        )
        
        # Only update if new progress is greater
        if progress_seconds > progress.video_progress_seconds:
            progress.video_progress_seconds = progress_seconds
        
        # Add to total watch duration
        progress.video_watch_duration += watch_duration
        progress.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Lesson.DoesNotExist:
        return JsonResponse({'error': 'Lesson not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Team Views
def team(request):
    """Display team members"""
    instructors = Instructor.objects.filter(is_active=True).order_by('display_order')
    
    # Group by role
    lead_instructors = instructors.filter(role='lead')
    senior_instructors = instructors.filter(role='senior')
    assistant_instructors = instructors.filter(role='assistant')
    
    context = {
        'lead_instructors': lead_instructors,
        'senior_instructors': senior_instructors,
        'assistant_instructors': assistant_instructors,
        'title': 'Our Team - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'team/team_list.html', context)

def instructor_detail(request, instructor_id):
    """Display instructor details"""
    instructor = get_object_or_404(Instructor, id=instructor_id, is_active=True)
    courses_teaching = instructor.courses.filter(is_active=True)
    
    context = {
        'instructor': instructor,
        'courses_teaching': courses_teaching,
        'title': f'{instructor.full_name} - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'team/team_detail.html', context)


# Blog Views
def blog(request):
    """Display blog posts"""
    category = request.GET.get('category', '')
    
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')
    
    if category:
        posts = posts.filter(category=category)
    
    # Pagination
    paginator = Paginator(posts, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Recent posts for sidebar
    recent_posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')[:5]
    
    context = {
        'posts': page_obj,
        'recent_posts': recent_posts,
        'categories': BlogPost.CATEGORIES,
        'selected_category': category,
        'title': 'Blog - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'blog/blog_list.html', context)

def blog_detail(request, slug):
    """Display single blog post"""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    
    # Increment views
    post.views += 1
    post.save()
    
    # Related posts
    related_posts = BlogPost.objects.filter(
        category=post.category,
        is_published=True
    ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'title': f'{post.title} - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'blog/blog_detail.html', context)

# Gallery Views
def gallery(request):
    """Display gallery images"""
    category = request.GET.get('category', '')
    
    gallery_items = Gallery.objects.all().order_by('-uploaded_at')
    
    if category:
        gallery_items = gallery_items.filter(category=category)
    
    # Group by category for filtering
    categories = Gallery.CATEGORIES
    
    context = {
        'gallery_items': gallery_items,
        'categories': categories,
        'selected_category': category,
        'title': 'Gallery - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'gallery/gallery_list.html', context)

# FAQ Views
def faq(request):
    """Display frequently asked questions"""
    faqs = FAQ.objects.filter(is_active=True).order_by('display_order', 'category')
    
    # Group by category
    faq_by_category = {}
    for faq_item in faqs:
        category = faq_item.get_category_display()
        if category not in faq_by_category:
            faq_by_category[category] = []
        faq_by_category[category].append(faq_item)
    
    context = {
        'faq_by_category': faq_by_category,
        'title': 'Frequently Asked Questions - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'faq/faq_list.html', context)

# Donation Views
def donate(request):
    """Display donation page"""
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            
            # Generate transaction ID
            import uuid
            donation.transaction_id = f"DON-{uuid.uuid4().hex[:10].upper()}"
            
            donation.save()
            
            # Send confirmation email
            send_mail(
                subject=f'Donation Confirmation - {donation.transaction_id}',
                message=f'''Assalamu Alaikum {donation.donor_name},

Thank you for your generous donation of ৳{donation.amount} to Taw Haa Zin Nurain Online Madarasa.

Transaction ID: {donation.transaction_id}
Amount: ৳{donation.amount}
Date: {donation.donated_at.strftime("%d %B, %Y %I:%M %p")}
Purpose: {donation.purpose if donation.purpose else 'General Donation'}

Your donation will help us continue our mission of providing authentic Islamic education to students worldwide.

May Allah accept your donation and reward you abundantly in this life and the Hereafter.

JazakAllah Khair,
Taw Haa Zin Nurain Online Madarasa Team''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[donation.donor_email],
                fail_silently=True,
            )
            
            messages.success(request, 'Thank you for your donation! A confirmation email has been sent.')
            return redirect('core:donation_success', transaction_id=donation.transaction_id)
    else:
        form = DonationForm()
    
    # Donation stats
    donation_stats = {
        'total_donations': Donation.objects.filter(is_verified=True).count(),
        'total_amount': Donation.objects.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0,
        'zakat_collected': Donation.objects.filter(is_zakat=True, is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    context = {
        'form': form,
        'donation_stats': donation_stats,
        'title': 'Donate - Support Islamic Education',
    }
    return render(request, 'donation/donate.html', context)

def donation_success(request, transaction_id):
    """Display donation success page"""
    donation = get_object_or_404(Donation, transaction_id=transaction_id)
    
    context = {
        'donation': donation,
        'title': 'Donation Successful - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'donation/success.html', context)

# Authentication Views
def register(request):
    """User registration view"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)
        
        if user_form.is_valid() and student_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            # Create student profile
            student = student_form.save(commit=False)
            student.user = user
            student.save()
            
            # Log the user in
            login(request, user)
            
            messages.success(request, 'Registration successful! Welcome to Taw Haa Zin Nurain Online Madarasa.')
            return redirect('dashboard')
    else:
        user_form = UserRegistrationForm()
        student_form = StudentRegistrationForm()
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'title': 'Register - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'auth/register.html', context)

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'core:dashboard')
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'title': 'Login - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'auth/login.html', context)

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:home')

# Dashboard Views
@login_required
def dashboard(request):
    """Student dashboard view"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    
    # Get enrollments
    enrollments = student.enrollments.select_related('course', 'assigned_instructor').all()
    active_enrollments = enrollments.filter(enrollment_status='active')
    
    # Calculate overall progress
    overall_progress = 0
    if active_enrollments.exists():
        overall_progress = active_enrollments.aggregate(Avg('overall_progress'))['overall_progress__avg'] or 0
    
    # Get attendance rate (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_enrollments = active_enrollments.filter(updated_at__gte=thirty_days_ago)
    attendance_rate = 0
    if recent_enrollments.exists():
        attendance_rate = recent_enrollments.aggregate(Avg('attendance_percentage'))['attendance_percentage__avg'] or 0
    
    # Calculate due amount
    due_amount = enrollments.filter(payment_status__in=['pending', 'partial']).aggregate(
        total_due=Sum('due_amount')
    )['total_due'] or 0
    
    # Get upcoming classes (mock data - you'd need a ClassSchedule model)
    upcoming_classes = []  # This would come from a ClassSchedule model
    
    # Get payment reminders
    payment_reminders = []
    for enrollment in enrollments.filter(payment_status__in=['pending', 'partial']):
        if enrollment.next_installment_date and enrollment.next_installment_date <= timezone.now().date() + timedelta(days=7):
            payment_reminders.append({
                'enrollment': enrollment,
                'amount_due': enrollment.due_amount,
                'due_date': enrollment.next_installment_date,
            })
    
    # Get completion alerts
    completion_alerts = []
    for enrollment in enrollments.filter(enrollment_status='active', overall_progress__gte=80):
        completion_alerts.append({
            'enrollment_id': enrollment.id,
            'course': enrollment.course.name,
            'score': enrollment.overall_progress,
        })
    
    # Get recent activities
    recent_activities = []
    for enrollment in enrollments.order_by('-updated_at')[:5]:
        recent_activities.append({
            'date': enrollment.updated_at,
            'description': f'Updated progress in {enrollment.course.name}',
            'course': enrollment.course.name,
            'status': enrollment.get_enrollment_status_display(),
            'status_color': 'success' if enrollment.enrollment_status == 'completed' else 'primary',
        })
    
    context = {
        'student': student,
        'enrolled_courses': enrollments,
        'active_courses': active_enrollments.count(),
        'overall_progress': overall_progress,
        'attendance_rate': attendance_rate,
        'due_amount': due_amount,
        'upcoming_classes': upcoming_classes,
        'payment_reminders': payment_reminders,
        'completion_alerts': completion_alerts,
        'recent_activities': recent_activities,
        'title': 'Dashboard - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/overview.html', context)

@login_required
def my_courses(request):
    """Display user's enrolled courses"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    enrollments = student.enrollments.select_related('course', 'assigned_instructor').all()
    
    context = {
        'enrollments': enrollments,
        'title': 'My Courses - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/my_courses.html', context)

@login_required
def my_progress(request):
    """Display user's progress tracking"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    enrollments = student.enrollments.select_related('course').filter(enrollment_status='active')
    
    # Prepare data for charts
    progress_data = []
    for enrollment in enrollments:
        progress_data.append({
            'course_name': enrollment.course.name,
            'progress': enrollment.overall_progress,
            'attendance': enrollment.attendance_percentage,
            'assignments': enrollment.assignment_completion,
        })
    
    context = {
        'enrollments': enrollments,
        'progress_data': progress_data,
        'title': 'My Progress - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/my_progress.html', context)

@login_required
def payment_history(request):
    """Display user's payment history"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    enrollments = student.enrollments.all()
    
    # Get all payments for user's enrollments
    payments = Payment.objects.filter(enrollment__in=enrollments).order_by('-payment_date')
    due_enrollments = enrollments.filter(payment_status__in=['pending', 'partial'])

    context = {
        'payments': payments,
        'total_paid': payments.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_due': enrollments.filter(payment_status__in=['pending', 'partial']).aggregate(Sum('due_amount'))['due_amount__sum'] or 0,
        'due_enrollments': due_enrollments,  # <-- pass this

        'title': 'Payment History - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/payment_history.html', context)

@login_required
def make_payment(request, enrollment_id):
    """Make payment for an enrollment"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user.student_profile)
    
    if enrollment.payment_status == 'paid':
        messages.info(request, 'This enrollment is already fully paid.')
        return redirect('payment_history')
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.enrollment = enrollment
            
            # Generate transaction ID
            import uuid
            payment.transaction_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
            
            payment.save()
            
            # Send payment confirmation email
            send_mail(
                subject=f'Payment Confirmation - {payment.transaction_id}',
                message=f'''Assalamu Alaikum {enrollment.student.full_name},

Thank you for your payment of ৳{payment.amount} for {enrollment.course.name}.

Payment Details:
Transaction ID: {payment.transaction_id}
Amount: ৳{payment.amount}
Payment Method: {payment.get_payment_method_display()}
Date: {payment.payment_date.strftime("%d %B, %Y %I:%M %p")}
Course: {enrollment.course.name}

Your payment is being processed and will be verified shortly. Once verified, you will receive another confirmation.

Thank you for choosing Taw Haa Zin Nurain Online Madarasa.

Best regards,
Accounts Department
Taw Haa Zin Nurain Online Madarasa''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
            
            messages.success(request, 'Payment submitted successfully! Please wait for verification.')
            return redirect('core:payment_success', transaction_id=payment.transaction_id)
    else:
        form = PaymentForm(initial={
            'amount': enrollment.due_amount,
        })
    
    context = {
        'enrollment': enrollment,
        'form': form,
        'title': 'Make Payment - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/make_payment.html', context)

@login_required
def payment_success(request, transaction_id):
    """Display payment success page"""
    payment = get_object_or_404(Payment, transaction_id=transaction_id)
    
    context = {
        'payment': payment,
        'title': 'Payment Successful - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/payment_success.html', context)

@login_required
def certificates(request):
    """Display user's certificates"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    completed_enrollments = student.enrollments.filter(
        enrollment_status='completed',
        completion_certificate_issued=True
    )
    
    context = {
        'certificates': completed_enrollments,
        'title': 'My Certificates - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/certificates.html', context)

@login_required
def download_certificate(request, enrollment_id):
    """Download certificate PDF"""
    enrollment = get_object_or_404(
        Enrollment, 
        id=enrollment_id, 
        student=request.user.student_profile,
        completion_certificate_issued=True
    )
    
    # Generate PDF certificate (you'll need to implement this)
    # For now, return a placeholder
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate-{enrollment.id}.pdf"'
    
    # You would use reportlab or other PDF library here
    # response.write(pdf_content)
    
    return response

@login_required
def schedule(request):
    """Display user's class schedule"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    
    # Get upcoming classes for active enrollments
    active_enrollments = student.enrollments.filter(enrollment_status='active')
    
    # This would come from a ClassSchedule model
    # For now, create mock schedule
    schedule_data = []
    for enrollment in active_enrollments:
        # Assuming classes are weekly
        schedule_data.append({
            'course': enrollment.course.name,
            'day': 'Monday, Wednesday, Friday',
            'time': '8:00 PM - 9:00 PM',
            'instructor': enrollment.assigned_instructor.full_name if enrollment.assigned_instructor else 'To be assigned',
            'join_link': '#',
        })
    
    context = {
        'schedule': schedule_data,
        'title': 'My Schedule - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'dashboard/schedule.html', context)



@login_required
def profile_settings(request):
    """Simplified user profile settings"""
    student = getattr(request.user, 'student_profile', None)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            
            if student:
                student_form = StudentUpdateForm(request.POST, request.FILES, instance=student)
            else:
                student_form = StudentRegistrationForm(request.POST, request.FILES)
            
            if user_form.is_valid() and student_form.is_valid():
                user_form.save()
                
                if student:
                    student_form.save()
                    messages.success(request, 'Profile updated successfully!')
                else:
                    student = student_form.save(commit=False)
                    student.user = request.user
                    student.student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
                    student.save()
                    messages.success(request, 'Student profile created successfully!')
                
                return redirect('core:profile_settings')
            else:
                messages.error(request, 'Please correct the errors below.')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('core:profile_settings')
            else:
                messages.error(request, 'Please correct password errors.')
    
    else:
        # GET request - initialize forms
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
        
        if student:
            student_form = StudentUpdateForm(instance=student)
        else:
            student_form = StudentRegistrationForm()
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'title': 'Profile Settings',
    }
    
    return render(request, 'dashboard/profile_settings.html', context)




@login_required
@user_passes_test(lambda u: u.is_staff)
def student_profile(request, student_id):
    """Admin view for individual student profile"""
    student = get_object_or_404(Student, id=student_id)
    
    # Get enrollments
    enrollments = student.enrollments.select_related('course', 'assigned_instructor').all()
    active_enrollments = enrollments.filter(enrollment_status='active')
    completed_enrollments = enrollments.filter(enrollment_status='completed')
    
    # Calculate statistics
    total_courses = enrollments.count()
    active_courses = active_enrollments.count()
    completed_courses = completed_enrollments.count()
    
    # Calculate progress statistics
    overall_progress = 0
    if active_enrollments.exists():
        overall_progress = active_enrollments.aggregate(
            Avg('overall_progress')
        )['overall_progress__avg'] or 0
    
    # Attendance statistics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_enrollments = active_enrollments.filter(updated_at__gte=thirty_days_ago)
    attendance_rate = 0
    if recent_enrollments.exists():
        attendance_rate = recent_enrollments.aggregate(
            Avg('attendance_percentage')
        )['attendance_percentage__avg'] or 0
    
    # Financial information
    payments = Payment.objects.filter(enrollment__student=student).order_by('-payment_date')
    total_paid = payments.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_due = enrollments.filter(payment_status__in=['pending', 'partial']).aggregate(Sum('due_amount'))['due_amount__sum'] or 0
    
    # Get certificates
    certificates = Certificate.objects.filter(enrollment__student=student).select_related('enrollment__course')
    
    # Recent activity
    recent_enrollments = enrollments.order_by('-updated_at')[:10]
    
    # Performance metrics
    performance_metrics = {
        'average_score': enrollments.aggregate(Avg('overall_progress'))['overall_progress__avg'] or 0,
        'completion_rate': (completed_courses / total_courses * 100) if total_courses > 0 else 0,
        'attendance_rate': attendance_rate,
        'payment_compliance': (total_paid / (total_paid + total_due) * 100) if (total_paid + total_due) > 0 else 100,
    }
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'overall_progress': overall_progress,
        'attendance_rate': attendance_rate,
        'payments': payments,
        'total_paid': total_paid,
        'total_due': total_due,
        'certificates': certificates,
        'recent_enrollments': recent_enrollments,
        'performance_metrics': performance_metrics,
        'title': f'Student Profile - {student.full_name}',
    }
    
    return render(request, 'dashboard/student_profile_admin.html', context)

# API Views for AJAX requests
@login_required
def get_dashboard_stats(request):
    """Get dashboard statistics for AJAX requests"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'active_courses': Course.objects.filter(is_active=True).count(),
        'total_enrollments': Enrollment.objects.count(),
        'completion_rate': Enrollment.objects.filter(enrollment_status='completed').count() / Enrollment.objects.count() * 100 if Enrollment.objects.count() > 0 else 0,
        'total_revenue': Payment.objects.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    return JsonResponse(stats)

@login_required
def check_payment_reminders(request):
    """Check for payment reminders"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'has_reminders': False})
    
    student = request.user.student_profile
    enrollments = student.enrollments.filter(
        payment_status__in=['pending', 'partial'],
        next_installment_date__isnull=False,
        next_installment_date__lte=timezone.now().date() + timedelta(days=3)
    )
    
    has_reminders = enrollments.exists()
    message = ""
    
    if has_reminders:
        total_due = enrollments.aggregate(Sum('due_amount'))['due_amount__sum'] or 0
        message = f"You have {enrollments.count()} payment(s) due totaling ৳{total_due}. Please make payment to avoid interruption in your classes."
    
    return JsonResponse({
        'has_reminders': has_reminders,
        'message': message,
        'count': enrollments.count(),
    })

@login_required
def update_progress(request):
    """Update course progress (for instructors)"""
    if request.method == 'POST' and request.user.is_staff:
        data = json.loads(request.body)
        enrollment_id = data.get('enrollment_id')
        attendance = data.get('attendance')
        assignments = data.get('assignments')
        
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        if attendance is not None:
            enrollment.attendance_percentage = attendance
        
        if assignments is not None:
            enrollment.assignment_completion = assignments
        
        enrollment.update_progress()
        enrollment.save()
        
        return JsonResponse({
            'success': True,
            'progress': enrollment.overall_progress,
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# About View
def about(request):
    """About page view"""
    context = {
        'title': 'About Us - Taw Haa Zin Nurain Online Madarasa',
        'mission': 'An Enlighten Generation, is Our Commitment',
        'vision': 'To provide authentic Islamic education to students worldwide through qualified scholars and modern technology.',
    }
    return render(request, 'core/about.html', context)

# Search View
def search(request):
    """Search functionality"""
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        # Search courses
        courses_results = Course.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query),
            is_active=True
        )[:10]
        
        # Search blog posts
        blog_results = BlogPost.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query),
            is_published=True
        )[:10]
        
        # Search instructors
        instructor_results = Instructor.objects.filter(
            Q(full_name__icontains=query) |
            Q(bio__icontains=query) |
            Q(specialization__icontains=query),
            is_active=True
        )[:10]
        
        results = {
            'courses': courses_results,
            'blog_posts': blog_results,
            'instructors': instructor_results,
            'query': query,
        }
    
    context = {
        'results': results,
        'title': f'Search Results: {query} - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'search/results.html', context)


# Update the existing contact view with more functionality
def contact(request):
    """Contact page view with improved functionality"""
    if request.method == 'POST':
        form = ContactForm(request.POST, user=request.user)
        if form.is_valid():
            contact_message = form.save(commit=False)
            
            # Associate with user if logged in
            if request.user.is_authenticated:
                contact_message.email = request.user.email
                if hasattr(request.user, 'student_profile'):
                    contact_message.student = request.user.student_profile
            
            contact_message.save()
            
            # Send notification email to admin
            send_mail(
                subject=f'New Contact Message: {contact_message.subject}',
                message=f'''New contact message received:

From: {contact_message.name}
Email: {contact_message.email}
Phone: {contact_message.phone if contact_message.phone else 'Not provided'}
Subject Type: {contact_message.get_subject_type_display()}
Subject: {contact_message.subject}
Priority: {contact_message.get_priority_display()}
Message: {contact_message.message}

Received: {contact_message.received_at.strftime("%Y-%m-%d %H:%M:%S")}

You can view and respond to this message in the admin panel.''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
            
            # Send auto-reply to sender
            send_mail(
                subject=f'We received your message - Taw Haa Zin Nurain Online Madarasa',
                message=f'''Assalamu Alaikum {contact_message.name},

Thank you for contacting Taw Haa Zin Nurain Online Madarasa.

We have received your message and our team will review it shortly. We strive to respond to all inquiries within 24-48 hours.

Message Reference: {contact_message.id}
Subject: {contact_message.subject}
Received: {contact_message.received_at.strftime("%d %B, %Y %I:%M %p")}

If your inquiry is urgent, please call us at +8801740433580.

Best regards,
Taw Haa Zin Nurain Online Madarasa Team''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact_message.email],
                fail_silently=True,
            )
            
            messages.success(request, 'Thank you for your message! We have sent you a confirmation email.')
            return redirect('contact')
    else:
        form = ContactForm(user=request.user)
    
    # Office locations
    offices = Office.objects.filter(is_active=True)
    
    # Contact statistics for display
    contact_stats = {
        'response_time': '24-48 hours',
        'phone': '+8801740433580',
        'email': 'info@tawhaa.edu.bd',
        'working_hours': '9:00 AM - 10:00 PM (Everyday)',
    }
    
    context = {
        'form': form,
        'offices': offices,
        'contact_stats': contact_stats,
        'title': 'Contact Us - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'contact/contact.html', context)



# Error Views
def handler404(request, exception):
    """404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """500 error handler"""
    return render(request, 'errors/500.html', status=500)

def handler403(request, exception):
    """403 error handler"""
    return render(request, 'errors/403.html', status=403)

def handler400(request, exception):
    """400 error handler"""
    return render(request, 'errors/400.html', status=400)

