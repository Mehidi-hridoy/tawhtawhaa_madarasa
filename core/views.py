from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Sum, Avg, Q, F, Prefetch
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
import uuid
from decimal import Decimal
from .models import *
from .forms import *
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import random
import string

# ==================== AUTHENTICATION VIEWS ====================
def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                full_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                email=user.email,
                phone=form.cleaned_data.get('phone', '')
            )
            
            # Log the user in
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to our platform.')
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form, 'title': 'Register'})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect based on user type
            if hasattr(user, 'instructor_profile'):
                return redirect('instructor:dashboard')
            elif hasattr(user, 'student_profile'):
                return redirect('core:dashboard')
            else:
                return redirect('core:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html', {'title': 'Login'})

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

# ==================== HOME & PUBLIC PAGES ====================
def home(request):
    """Home page with featured content"""
    featured_courses = Course.objects.filter(
        is_active=True, 
        is_featured=True,
        is_approved=True
    ).order_by('-created_at')[:8]
    
    new_courses = Course.objects.filter(
        is_active=True,
        is_approved=True
    ).order_by('-created_at')[:6]
    
    free_courses = Course.objects.filter(
        is_active=True,
        is_approved=True,
        price_type='free'
    ).order_by('-created_at')[:6]
    
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True, courses__is_approved=True))
    ).order_by('-course_count')[:8]
    
    top_instructors = Instructor.objects.filter(
        is_active=True,
        is_verified=True
    ).annotate(
        course_count=Count('instructor_courses', filter=Q(instructor_courses__course__is_active=True))
    ).order_by('-course_count')[:6]
    
    testimonials = CourseReview.objects.filter(
        rating=5,
        is_published=True
    ).select_related('student', 'course')[:4]
    
    context = {
        'featured_courses': featured_courses,
        'new_courses': new_courses,
        'free_courses': free_courses,
        'categories': categories,
        'top_instructors': top_instructors,
        'testimonials': testimonials,
        'title': 'Online Learning Platform - Learn Anything, Anytime'
    }
    return render(request, 'core/home.html', context)

def about(request):
    """About page"""
    instructors_count = Instructor.objects.filter(is_active=True).count()
    students_count = Student.objects.filter(is_active=True).count()
    courses_count = Course.objects.filter(is_active=True, is_approved=True).count()
    
    context = {
        'title': 'About Us',
        'instructors_count': instructors_count,
        'students_count': students_count,
        'courses_count': courses_count,
    }
    return render(request, 'core/about.html', context)

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            
            if request.user.is_authenticated:
                contact_message.email = request.user.email
                if hasattr(request.user, 'student_profile'):
                    contact_message.student = request.user.student_profile
            
            contact_message.save()
            
            # Send notification email
            send_mail(
                subject=f'New Contact: {contact_message.subject}',
                message=f'From: {contact_message.name}\nEmail: {contact_message.email}\nMessage: {contact_message.message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=True,
            )
            
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form, 'title': 'Contact Us'})

def search(request):
    """Search functionality"""
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        # Search courses
        results['courses'] = Course.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query),
            is_active=True,
            is_approved=True
        )[:10]
        
        # Search instructors
        results['instructors'] = Instructor.objects.filter(
            Q(full_name__icontains=query) |
            Q(bio__icontains=query) |
            Q(specialization__icontains=query),
            is_active=True
        )[:10]
        
        # Search blog posts
        results['blog_posts'] = BlogPost.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query),
            is_published=True
        )[:10]
    
    context = {
        'results': results,
        'query': query,
        'title': f'Search Results: {query}'
    }
    return render(request, 'core/search.html', context)

# ==================== COURSE VIEWS ====================
def courses(request):
    """Browse all courses"""
    category_slug = request.GET.get('category', '')
    level = request.GET.get('level', '')
    price = request.GET.get('price', '')
    rating = request.GET.get('rating', '')
    sort = request.GET.get('sort', 'newest')
    
    courses_qs = Course.objects.filter(is_active=True, is_approved=True)
    
    # Filters
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        courses_qs = courses_qs.filter(category=category)
    
    if level and level != 'all':
        courses_qs = courses_qs.filter(level=level)
    
    if price == 'free':
        courses_qs = courses_qs.filter(price_type='free')
    elif price == 'paid':
        courses_qs = courses_qs.filter(price_type='paid')
    
    if rating:
        courses_qs = courses_qs.filter(average_rating__gte=float(rating))
    
    # Sorting
    if sort == 'popular':
        courses_qs = courses_qs.order_by('-enrollment_count')
    elif sort == 'highest_rated':
        courses_qs = courses_qs.order_by('-average_rating')
    elif sort == 'price_low':
        courses_qs = courses_qs.order_by('base_price')
    elif sort == 'price_high':
        courses_qs = courses_qs.order_by('-base_price')
    else:  # newest
        courses_qs = courses_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(courses_qs, 12)
    page = request.GET.get('page', 1)
    try:
        courses_page = paginator.page(page)
    except:
        courses_page = paginator.page(1)
    
    categories = Category.objects.filter(is_active=True).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True))
    )
    
    context = {
        'courses': courses_page,
        'categories': categories,
        'selected_category': category_slug,
        'selected_level': level,
        'selected_price': price,
        'selected_rating': rating,
        'selected_sort': sort,
        'title': 'Browse All Courses'
    }
    return render(request, 'courses/browse.html', context)

def course_detail(request, course_slug):
    """Course detail page"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True, is_approved=True)
    
    # Check if user is enrolled
    is_enrolled = False
    enrollment = None
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        enrollment = Enrollment.objects.filter(
            student=request.user.student_profile,
            course=course,
            enrollment_status__in=['active', 'completed']
        ).first()
        is_enrolled = enrollment is not None
    
    # Get course content preview
    modules = course.modules.filter(is_published=True).order_by('order')[:5]
    
    # Get instructor details
    instructors = course.course_instructors.select_related('instructor').filter(
        instructor__is_active=True
    ).order_by('display_order')
    
    # Get reviews
    reviews = CourseReview.objects.filter(
        course=course,
        is_published=True
    ).order_by('-created_at')[:5]
    
    # Related courses
    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True,
        is_approved=True
    ).exclude(id=course.id)[:4]
    
    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        in_wishlist = Wishlist.objects.filter(
            student=request.user.student_profile,
            course=course
        ).exists()
    
    context = {
        'course': course,
        'modules': modules,
        'instructors': instructors,
        'reviews': reviews,
        'related_courses': related_courses,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'in_wishlist': in_wishlist,
        'title': f'{course.name} - Online Course'
    }
    return render(request, 'courses/detail.html', context)

@login_required
def enroll_course(request, course_slug):
    """Enroll in a course"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True, is_approved=True)
    student = get_object_or_404(Student, user=request.user)
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        enrollment_status__in=['active', 'pending', 'completed']
    ).first()
    
    if existing_enrollment:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('core:course_detail', course_slug=course.slug)
    
    # Handle free courses
    if course.price_type == 'free' or course.get_current_price() == 0:
        # Create enrollment for free course
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            enrollment_status='active',
            payment_status='paid',
            start_date=timezone.now().date(),
            amount_paid=0
        )
        
        # Send enrollment notification
        Notification.objects.create(
            recipient=request.user,
            notification_type='enrollment',
            title=f'Enrolled in {course.name}',
            message=f'You have successfully enrolled in {course.name}. Start learning now!',
            enrollment=enrollment,
            course=course
        )
        
        messages.success(request, f'Successfully enrolled in {course.name}!')
        return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    # For paid courses, show checkout page
    if request.method == 'POST':
        # Process coupon if provided
        coupon_code = request.POST.get('coupon_code', '').strip()
        coupon = None
        discount_amount = Decimal('0.00')
        
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                is_valid, message = coupon.is_valid(request.user, course)
                if is_valid:
                    discount_amount = coupon.calculate_discount(course.get_current_price())
                else:
                    messages.error(request, message)
                    return redirect('core:enroll_course', course_slug=course.slug)
            except Coupon.DoesNotExist:
                messages.error(request, 'Invalid coupon code')
                return redirect('core:enroll_course', course_slug=course.slug)
        
        # Calculate final amount
        final_amount = course.get_current_price() - discount_amount
        
        # Create enrollment with pending status
        enrollment = Enrollment.objects.create(
            student=student,
            course=course,
            enrollment_status='pending',
            payment_status='pending'
        )
        
        # Store in session for checkout
        request.session['enrollment_id'] = str(enrollment.id)
        request.session['course_id'] = str(course.id)
        request.session['final_amount'] = str(final_amount)
        request.session['coupon_code'] = coupon_code if coupon else ''
        
        return redirect('core:checkout')
    
    # GET request - show enrollment form
    context = {
        'course': course,
        'student': student,
        'title': f'Enroll in {course.name}'
    }
    return render(request, 'courses/enroll.html', context)

# ==================== PAYMENT & CHECKOUT ====================
@login_required
def checkout(request):
    """Checkout and payment page"""
    enrollment_id = request.session.get('enrollment_id')
    course_id = request.session.get('course_id')
    final_amount = request.session.get('final_amount', '0')
    coupon_code = request.session.get('coupon_code', '')
    
    if not enrollment_id or not course_id:
        messages.error(request, 'Invalid checkout session')
        return redirect('core:courses')
    
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id, student__user=request.user)
        course = Course.objects.get(id=course_id)
    except (Enrollment.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Invalid enrollment')
        return redirect('core:courses')
    
    # Calculate amounts
    base_price = course.get_current_price()
    discount_amount = Decimal(base_price) - Decimal(final_amount)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id', '').strip()
        
        if not transaction_id:
            messages.error(request, 'Please provide a transaction ID')
            return redirect('core:checkout')
        
        # Generate a unique transaction ID if needed
        if transaction_id == 'auto':
            transaction_id = f"TXN{str(uuid.uuid4())[:8].upper()}"
        
        # Create payment record
        payment = Payment.objects.create(
            enrollment=enrollment,
            student=enrollment.student,
            amount=final_amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='completed',  # Auto-verify for demo
            is_verified=True,
            verified_at=timezone.now(),
            verified_by=request.user
        )
        
        # Update enrollment
        enrollment.payment_status = 'paid'
        enrollment.enrollment_status = 'active'
        enrollment.start_date = timezone.now().date()
        enrollment.amount_paid = final_amount
        enrollment.save()
        
        # Update coupon usage
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass
        
        # Clear session
        request.session.pop('enrollment_id', None)
        request.session.pop('course_id', None)
        request.session.pop('final_amount', None)
        request.session.pop('coupon_code', None)
        
        # Send notification
        Notification.objects.create(
            recipient=request.user,
            notification_type='payment',
            title='Payment Successful',
            message=f'Your payment of ৳{final_amount} for {course.name} has been processed successfully.',
            enrollment=enrollment,
            course=course
        )
        
        messages.success(request, f'Payment successful! You are now enrolled in {course.name}.')
        return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    context = {
        'enrollment': enrollment,
        'course': course,
        'base_price': base_price,
        'discount_amount': discount_amount,
        'final_amount': final_amount,
        'coupon_code': coupon_code,
        'title': 'Checkout'
    }
    return render(request, 'payment/checkout.html', context)

@login_required
def payment_success(request, transaction_id):
    """Payment success page"""
    payment = get_object_or_404(Payment, transaction_id=transaction_id, student__user=request.user)
    
    context = {
        'payment': payment,
        'title': 'Payment Successful'
    }
    return render(request, 'payment/success.html', context)

# ==================== LEARNING DASHBOARD ====================
@login_required
def learning_dashboard(request, enrollment_id):
    """Main learning dashboard"""
    enrollment = get_object_or_404(
        Enrollment, 
        id=enrollment_id, 
        student__user=request.user,
        enrollment_status__in=['active', 'completed']
    )
    
    course = enrollment.course
    student = enrollment.student
    
    # Get or create course progress
    course_progress, created = StudentCourseProgress.objects.get_or_create(
        student=student,
        course=course
    )
    
    # Get modules and lessons with progress
    modules = course.modules.filter(is_published=True).order_by('order')
    
    # Calculate overall progress
    total_required_lessons = Lesson.objects.filter(
        module__course=course,
        is_published=True,
        require_completion=True
    ).count()
    
    completed_lessons = StudentLessonProgress.objects.filter(
        student=student,
        lesson__module__course=course,
        status='completed',
        enrollment=enrollment
    ).count()
    
    progress_percentage = 0
    if total_required_lessons > 0:
        progress_percentage = (completed_lessons / total_required_lessons) * 100
    
    # Update enrollment progress
    enrollment.progress_percentage = progress_percentage
    enrollment.last_accessed = timezone.now()
    enrollment.save()
    
    # Update course progress
    course_progress.overall_progress = progress_percentage
    course_progress.completed_lessons = completed_lessons
    course_progress.last_accessed = timezone.now()
    course_progress.save()
    
    # Get recent activity
    recent_progress = StudentLessonProgress.objects.filter(
        student=student,
        enrollment=enrollment
    ).order_by('-last_accessed')[:5]
    
    # Get next lesson to continue
    next_lesson = None
    if progress_percentage < 100:
        # Find first incomplete lesson
        for module in modules:
            for lesson in module.lessons.filter(is_published=True, require_completion=True):
                progress, created = StudentLessonProgress.objects.get_or_create(
                    student=student,
                    lesson=lesson,
                    enrollment=enrollment,
                    defaults={'status': 'not_started'}
                )
                if progress.status != 'completed':
                    next_lesson = lesson
                    break
            if next_lesson:
                break
    
    context = {
        'enrollment': enrollment,
        'course': course,
        'modules': modules,
        'student': student,
        'course_progress': course_progress,
        'progress_percentage': progress_percentage,
        'completed_lessons': completed_lessons,
        'total_lessons': total_required_lessons,
        'recent_progress': recent_progress,
        'next_lesson': next_lesson,
        'title': f'Learning - {course.name}'
    }
    return render(request, 'learning/dashboard.html', context)

@login_required
def lesson_view(request, enrollment_id, lesson_id):
    """View a lesson"""
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student__user=request.user,
        enrollment_status__in=['active', 'completed']
    )
    
    lesson = get_object_or_404(
        Lesson,
        id=lesson_id,
        module__course=enrollment.course,
        is_published=True
    )
    
    # Get or create lesson progress
    lesson_progress, created = StudentLessonProgress.objects.get_or_create(
        student=enrollment.student,
        lesson=lesson,
        enrollment=enrollment,
        defaults={'status': 'in_progress', 'started_at': timezone.now()}
    )
    
    # Update progress status
    if lesson_progress.status == 'not_started':
        lesson_progress.status = 'in_progress'
        lesson_progress.started_at = timezone.now()
    
    # Update last accessed
    lesson_progress.last_accessed = timezone.now()
    lesson_progress.save()
    
    # Get module info
    module = lesson.module
    course = enrollment.course
    
    # Get all lessons in module for navigation
    module_lessons = list(module.lessons.filter(is_published=True).order_by('order'))
    
    # Find current position
    current_index = None
    for i, l in enumerate(module_lessons):
        if l.id == lesson.id:
            current_index = i
            break
    
    # Navigation
    prev_lesson = None
    next_lesson = None
    
    if current_index is not None:
        if current_index > 0:
            prev_lesson = module_lessons[current_index - 1]
        if current_index < len(module_lessons) - 1:
            next_lesson = module_lessons[current_index + 1]
    
    # Get interactive MCQs for this lesson
    interactive_mcqs = InteractiveMCQ.objects.filter(
        lesson=lesson,
        is_active=True
    ).order_by('appear_at_second')
    
    # Get quiz if exists
    quiz = None
    if hasattr(lesson, 'quiz'):
        quiz = lesson.quiz
    
    # Get resources for this lesson
    resources = CourseResource.objects.filter(
        Q(course=course) | Q(lesson=lesson),
        is_active=True
    ).order_by('order')
    
    # Convert interactive MCQs to JSON for JavaScript
    mcqs_data = []
    for mcq in interactive_mcqs:
        mcqs_data.append({
            'id': str(mcq.id),
            'question': mcq.question,
            'type': mcq.question_type,
            'appear_at': mcq.appear_at_second,
            'time_limit': mcq.time_limit_seconds,
            'allow_skip': mcq.allow_skip,
            'max_attempts': mcq.max_attempts,
            'points': mcq.points_value,
            'options': [
                {
                    'id': str(option.id),
                    'text': option.text,
                    'is_correct': option.is_correct
                }
                for option in mcq.get_options()
            ]
        })
    
    context = {
        'enrollment': enrollment,
        'lesson': lesson,
        'lesson_progress': lesson_progress,
        'module': module,
        'course': course,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'interactive_mcqs': interactive_mcqs,
        'mcqs_json': json.dumps(mcqs_data),
        'quiz': quiz,
        'resources': resources,
        'youtube_id': lesson.get_youtube_id(),
        'title': f'{lesson.title} - {course.name}'
    }
    return render(request, 'learning/lesson.html', context)

# ==================== API VIEWS ====================
@login_required
@require_POST
@csrf_exempt
def submit_mcq_response(request):
    """Submit response for interactive MCQ"""
    try:
        data = json.loads(request.body)
        mcq_id = data.get('mcq_id')
        selected_option_ids = data.get('selected_options', [])
        enrollment_id = data.get('enrollment_id')
        
        mcq = InteractiveMCQ.objects.get(id=mcq_id)
        enrollment = Enrollment.objects.get(id=enrollment_id, student__user=request.user)
        student = enrollment.student
        
        # Get selected options
        selected_options = MCQOption.objects.filter(id__in=selected_option_ids)
        
        # Check if answer is correct
        is_correct = True
        correct_options = mcq.get_options().filter(is_correct=True)
        
        if mcq.question_type == 'single':
            is_correct = (selected_options.count() == 1 and 
                         selected_options.first().is_correct)
        else:  # multiple
            selected_correct = selected_options.filter(is_correct=True).count()
            is_correct = (selected_correct == correct_options.count() and 
                         selected_options.count() == correct_options.count())
        
        # Calculate points
        points_earned = mcq.points_value if is_correct else 0
        
        # Save response
        response = StudentMCQResponse.objects.create(
            student=student,
            mcq=mcq,
            is_correct=is_correct,
            points_earned=points_earned,
            response_time_seconds=data.get('response_time', 0)
        )
        response.selected_options.set(selected_options)
        
        # Update lesson progress
        lesson_progress, created = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=mcq.lesson,
            enrollment=enrollment
        )
        lesson_progress.points_earned += points_earned
        lesson_progress.save()
        
        return JsonResponse({
            'success': True,
            'is_correct': is_correct,
            'points_earned': points_earned,
            'total_points': lesson_progress.points_earned,
            'explanations': [
                {
                    'option_id': str(opt.id),
                    'explanation': opt.explanation,
                    'is_correct': opt.is_correct
                }
                for opt in mcq.get_options() if opt.explanation
            ]
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
@csrf_exempt
def complete_lesson(request, lesson_id):
    """Mark lesson as completed"""
    try:
        lesson = Lesson.objects.get(id=lesson_id)
        student = request.user.student_profile
        
        # Find enrollment for this course
        enrollment = Enrollment.objects.get(
            student=student,
            course=lesson.module.course,
            enrollment_status__in=['active', 'completed']
        )
        
        # Get or create lesson progress
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            enrollment=enrollment
        )
        
        # Mark as completed
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.points_earned += lesson.points_value
        progress.save()
        
        # Update course progress
        course_progress, created = StudentCourseProgress.objects.get_or_create(
            student=student,
            course=lesson.module.course
        )
        course_progress.update_progress()
        
        # Update enrollment progress
        enrollment.update_progress()
        
        # Check if course is completed
        if enrollment.progress_percentage >= 100 and enrollment.enrollment_status == 'active':
            enrollment.enrollment_status = 'completed'
            enrollment.completed_at = timezone.now()
            enrollment.save()
            
            # Generate certificate if available
            if enrollment.course.certificate_available:
                certificate, created = Certificate.objects.get_or_create(
                    enrollment=enrollment,
                    defaults={
                        'student': student,
                        'course': enrollment.course,
                        'student_name': student.full_name,
                        'course_name': enrollment.course.name,
                        'completion_date': timezone.now().date(),
                        'final_score': enrollment.progress_percentage,
                    }
                )
                
                # Send notification
                Notification.objects.create(
                    recipient=request.user,
                    notification_type='certificate',
                    title='Course Completed!',
                    message=f'Congratulations! You have completed {enrollment.course.name}. Your certificate is ready.',
                    enrollment=enrollment,
                    course=enrollment.course
                )
        
        return JsonResponse({
            'success': True,
            'progress': enrollment.progress_percentage,
            'next_lesson_url': None  # You can implement next lesson logic here
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
@csrf_exempt
def save_video_progress(request):
    """Save video watch progress"""
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        enrollment_id = data.get('enrollment_id')
        current_time = data.get('current_time')
        duration = data.get('duration')
        
        lesson = Lesson.objects.get(id=lesson_id)
        enrollment = Enrollment.objects.get(id=enrollment_id, student__user=request.user)
        
        # Get or create lesson progress
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=enrollment.student,
            lesson=lesson,
            enrollment=enrollment
        )
        
        # Update video progress
        if current_time > progress.video_progress_seconds:
            progress.video_progress_seconds = current_time
        
        if duration:
            progress.video_total_watched = min(duration, progress.video_total_watched + 1)
        
        progress.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ==================== QUIZ VIEWS ====================
@login_required
def start_quiz(request, enrollment_id, quiz_id):
    """Start a quiz"""
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student__user=request.user,
        enrollment_status='active'
    )
    
    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        is_active=True,
        is_published=True
    )
    
    # Check if quiz belongs to enrolled course
    if quiz.lesson and quiz.lesson.module.course != enrollment.course:
        if quiz.module and quiz.module.course != enrollment.course:
            if quiz.course and quiz.course != enrollment.course:
                messages.error(request, 'You do not have access to this quiz')
                return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    # Check attempt limits
    previous_attempts = StudentQuizAttempt.objects.filter(
        student=enrollment.student,
        quiz=quiz,
        enrollment=enrollment
    ).count()
    
    if previous_attempts >= quiz.max_attempts:
        messages.error(request, f'You have reached the maximum attempts ({quiz.max_attempts}) for this quiz')
        return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    # Check availability dates
    now = timezone.now()
    if quiz.available_from and now < quiz.available_from:
        messages.error(request, 'This quiz is not yet available')
        return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    if quiz.available_until and now > quiz.available_until:
        messages.error(request, 'This quiz is no longer available')
        return redirect('core:learning_dashboard', enrollment_id=enrollment.id)
    
    # Create quiz attempt
    attempt = StudentQuizAttempt.objects.create(
        student=enrollment.student,
        quiz=quiz,
        enrollment=enrollment,
        attempt_number=previous_attempts + 1,
        total_questions=quiz.questions.count()
    )
    
    # Get questions
    questions = quiz.questions.filter(is_active=True)
    if quiz.randomize_questions:
        questions = questions.order_by('?')
    
    context = {
        'enrollment': enrollment,
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
        'title': f'Quiz: {quiz.title}'
    }
    return render(request, 'learning/quiz_start.html', context)

@login_required
@require_POST
def submit_quiz(request, attempt_id):
    """Submit quiz answers"""
    attempt = get_object_or_404(
        StudentQuizAttempt,
        id=attempt_id,
        student__user=request.user,
        is_completed=False
    )
    
    quiz = attempt.quiz
    data = request.POST
    
    # Process each question
    for key, value in data.items():
        if key.startswith('question_'):
            question_id = key.split('_')[1]
            try:
                question = QuizQuestion.objects.get(id=question_id, quiz=quiz)
                
                # Create response
                response = QuizResponse.objects.create(
                    attempt=attempt,
                    question=question
                )
                
                # Handle different question types
                if question.question_type in ['mcq_single', 'true_false']:
                    try:
                        option = QuestionOption.objects.get(id=value, question=question)
                        response.selected_options.add(option)
                        response.is_correct = option.is_correct
                        response.points_earned = question.points if option.is_correct else 0
                    except (ValueError, QuestionOption.DoesNotExist):
                        pass
                
                elif question.question_type == 'mcq_multiple':
                    option_ids = data.getlist(key)
                    selected_options = QuestionOption.objects.filter(
                        id__in=option_ids,
                        question=question
                    )
                    response.selected_options.set(selected_options)
                    
                    # Check if all correct options selected and no incorrect ones
                    correct_options = question.options.filter(is_correct=True)
                    selected_correct = selected_options.filter(is_correct=True).count()
                    
                    if (selected_correct == correct_options.count() and 
                        selected_options.count() == correct_options.count()):
                        response.is_correct = True
                        response.points_earned = question.points
                
                elif question.question_type in ['short_answer', 'essay']:
                    response.text_response = value
                    # Auto-grading not implemented for text responses
                    response.points_earned = 0
                
                response.save()
                
            except QuizQuestion.DoesNotExist:
                continue
    
    # Calculate final score
    attempt.calculate_score()
    attempt.is_completed = True
    attempt.submitted_at = timezone.now()
    attempt.save()
    
    # Update lesson progress if this is a lesson quiz
    if quiz.lesson:
        lesson_progress, created = StudentLessonProgress.objects.get_or_create(
            student=attempt.student,
            lesson=quiz.lesson,
            enrollment=attempt.enrollment
        )
        lesson_progress.quiz_score = attempt.score
        lesson_progress.attempts_count += 1
        if attempt.is_passed:
            lesson_progress.points_earned = quiz.lesson.points_value
        lesson_progress.save()
    
    return JsonResponse({
        'success': True,
        'score': attempt.score,
        'is_passed': attempt.is_passed,
        'correct': attempt.correct_answers,
        'total': attempt.total_questions
    })

# ==================== DASHBOARD VIEWS ====================
@login_required
def dashboard(request):
    """Student dashboard"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    
    # Get enrollments
    enrollments = student.enrollments.select_related('course').filter(
        enrollment_status__in=['active', 'completed']
    )
    
    # Calculate statistics
    total_courses = enrollments.count()
    active_courses = enrollments.filter(enrollment_status='active').count()
    completed_courses = enrollments.filter(enrollment_status='completed').count()
    
    # Calculate progress
    overall_progress = 0
    if enrollments.exists():
        overall_progress = enrollments.aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0
    
    # Get certificates
    certificates = Certificate.objects.filter(student=student)
    
    # Get recent activity
    recent_activity = StudentLessonProgress.objects.filter(
        student=student
    ).select_related('lesson', 'lesson__module__course').order_by('-last_accessed')[:10]
    
    # Get upcoming quizzes
    upcoming_quizzes = Quiz.objects.filter(
        course__enrollments__student=student,
        course__enrollments__enrollment_status='active',
        is_active=True,
        is_published=True,
        available_from__gte=timezone.now()
    )[:5]
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'total_courses': total_courses,
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'overall_progress': overall_progress,
        'certificates': certificates,
        'recent_activity': recent_activity,
        'upcoming_quizzes': upcoming_quizzes,
        'title': 'Dashboard'
    }
    return render(request, 'dashboard/overview.html', context)

@login_required
def my_courses(request):
    """Display user's enrolled courses"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    enrollments = student.enrollments.select_related('course').order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'title': 'My Courses'
    }
    return render(request, 'dashboard/my_courses.html', context)

@login_required
def my_progress(request):
    """Display user's progress"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    enrollments = student.enrollments.select_related('course').filter(
        enrollment_status__in=['active', 'completed']
    )
    
    # Prepare progress data for charts
    progress_data = []
    for enrollment in enrollments:
        course_progress, created = StudentCourseProgress.objects.get_or_create(
            student=student,
            course=enrollment.course
        )
        
        progress_data.append({
            'course': enrollment.course.name,
            'progress': enrollment.progress_percentage,
            'completed_lessons': course_progress.completed_lessons or 0,
            'total_lessons': Lesson.objects.filter(
                module__course=enrollment.course,
                is_published=True,
                require_completion=True
            ).count()
        })
    
    context = {
        'enrollments': enrollments,
        'progress_data': progress_data,
        'overall_progress': enrollments.aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0,
        'title': 'My Progress'
    }
    return render(request, 'dashboard/my_progress.html', context)

@login_required
def payment_history(request):
    """Display user's payment history"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    payments = Payment.objects.filter(student=student).order_by('-payment_date')
    
    context = {
        'payments': payments,
        'total_paid': payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        'title': 'Payment History'
    }
    return render(request, 'dashboard/payment_history.html', context)

@login_required
def certificates(request):
    """Display user's certificates"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    certificates = Certificate.objects.filter(student=student).select_related('course')
    
    context = {
        'certificates': certificates,
        'title': 'My Certificates'
    }
    return render(request, 'dashboard/certificates.html', context)

@login_required
def profile_settings(request):
    """User profile settings"""
    student = getattr(request.user, 'student_profile', None)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        student_form = StudentUpdateForm(request.POST, request.FILES, instance=student) if student else None
        
        if user_form.is_valid() and (student_form is None or student_form.is_valid()):
            user_form.save()
            
            if student_form:
                student_form.save()
            elif not student and 'phone' in request.POST:
                # Create student profile if doesn't exist
                Student.objects.create(
                    user=request.user,
                    full_name=f"{request.user.first_name} {request.user.last_name}",
                    phone=request.POST.get('phone'),
                    email=request.user.email
                )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:profile_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        student_form = StudentUpdateForm(instance=student) if student else None
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'student': student,
        'title': 'Profile Settings'
    }
    return render(request, 'dashboard/profile_settings.html', context)

# ==================== TEAM VIEWS ====================
def team(request):
    """Display team members"""
    instructors = Instructor.objects.filter(is_active=True).order_by('display_order')
    
    context = {
        'instructors': instructors,
        'title': 'Our Team'
    }
    return render(request, 'team/team.html', context)

def instructor_detail(request, instructor_id):
    """Display instructor details"""
    instructor = get_object_or_404(Instructor, id=instructor_id, is_active=True)
    
    # Get courses taught by this instructor
    courses_taught = Course.objects.filter(
        course_instructors__instructor=instructor,
        is_active=True,
        is_approved=True
    )
    
    context = {
        'instructor': instructor,
        'courses_taught': courses_taught,
        'title': f'{instructor.full_name} - Instructor Profile'
    }
    return render(request, 'team/instructor_detail.html', context)

# ==================== BLOG VIEWS ====================
def blog(request):
    """Display blog posts"""
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page = request.GET.get('page', 1)
    try:
        posts_page = paginator.page(page)
    except:
        posts_page = paginator.page(1)
    
    # Recent posts
    recent_posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')[:5]
    
    # Categories
    categories = BlogPost.objects.values('category').annotate(count=Count('category'))
    
    context = {
        'posts': posts_page,
        'recent_posts': recent_posts,
        'categories': categories,
        'title': 'Blog'
    }
    return render(request, 'blog/blog.html', context)

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
        'title': post.title
    }
    return render(request, 'blog/blog_detail.html', context)

# ==================== GALLERY VIEWS ====================
def gallery(request):
    """Display gallery"""
    gallery_items = Gallery.objects.all().order_by('-uploaded_at')
    
    # Group by category
    categories = Gallery.objects.values('category').annotate(count=Count('category'))
    
    context = {
        'gallery_items': gallery_items,
        'categories': categories,
        'title': 'Gallery'
    }
    return render(request, 'gallery/gallery.html', context)

# ==================== FAQ VIEWS ====================
def faq(request):
    """Display FAQs"""
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
        'title': 'Frequently Asked Questions'
    }
    return render(request, 'faq/faq.html', context)

# ==================== DONATION VIEWS ====================
def donate(request):
    """Donation page"""
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.transaction_id = f"DON{str(uuid.uuid4())[:8].upper()}"
            donation.save()
            
            messages.success(request, 'Thank you for your donation!')
            return redirect('core:donation_success', transaction_id=donation.transaction_id)
    else:
        form = DonationForm()
    
    context = {
        'form': form,
        'title': 'Donate'
    }
    return render(request, 'donation/donate.html', context)

def donation_success(request, transaction_id):
    """Donation success page"""
    donation = get_object_or_404(Donation, transaction_id=transaction_id)
    
    context = {
        'donation': donation,
        'title': 'Donation Successful'
    }
    return render(request, 'donation/success.html', context)

# ==================== API ENDPOINTS ====================
@login_required
@require_GET
def get_dashboard_stats(request):
    """Get dashboard statistics (for instructors/admins)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    stats = {
        'total_students': Student.objects.filter(is_active=True).count(),
        'total_courses': Course.objects.filter(is_active=True, is_approved=True).count(),
        'total_enrollments': Enrollment.objects.count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        'pending_enrollments': Enrollment.objects.filter(enrollment_status='pending').count(),
        'active_enrollments': Enrollment.objects.filter(enrollment_status='active').count(),
    }
    
    return JsonResponse(stats)

@login_required
@require_GET
def check_payment_reminders(request):
    """Check for payment reminders"""
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'has_reminders': False})
    
    student = request.user.student_profile
    pending_payments = Payment.objects.filter(
        student=student,
        status='pending'
    ).count()
    
    return JsonResponse({
        'has_reminders': pending_payments > 0,
        'count': pending_payments
    })

@login_required
@require_POST
def update_progress(request):
    """Update progress (for AJAX)"""
    try:
        data = json.loads(request.body)
        enrollment_id = data.get('enrollment_id')
        
        enrollment = Enrollment.objects.get(
            id=enrollment_id,
            student__user=request.user
        )
        
        # Recalculate progress
        enrollment.update_progress()
        
        return JsonResponse({
            'success': True,
            'progress': enrollment.progress_percentage
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# ==================== WISHLIST VIEWS ====================
@login_required
def wishlist(request):
    """Display user's wishlist"""
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    wishlist_items = Wishlist.objects.filter(student=student).select_related('course')
    
    context = {
        'wishlist_items': wishlist_items,
        'title': 'My Wishlist'
    }
    return render(request, 'wishlist/wishlist.html', context)

@login_required
@require_POST
def add_to_wishlist(request):
    """Add course to wishlist"""
    course_id = request.POST.get('course_id')
    course = get_object_or_404(Course, id=course_id, is_active=True)
    student = get_object_or_404(Student, user=request.user)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        student=student,
        course=course
    )
    
    if created:
        return JsonResponse({'success': True, 'message': 'Added to wishlist'})
    else:
        return JsonResponse({'success': False, 'message': 'Already in wishlist'})

@login_required
@require_POST
def remove_from_wishlist(request):
    """Remove course from wishlist"""
    course_id = request.POST.get('course_id')
    student = get_object_or_404(Student, user=request.user)
    
    deleted = Wishlist.objects.filter(
        student=student,
        course_id=course_id
    ).delete()
    
    if deleted[0] > 0:
        return JsonResponse({'success': True, 'message': 'Removed from wishlist'})
    else:
        return JsonResponse({'success': False, 'message': 'Item not found'})

# ==================== REVIEW VIEWS ====================
@login_required
def submit_review(request, course_slug):
    """Submit course review"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    student = get_object_or_404(Student, user=request.user)
    
    # Check if user has completed the course
    enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        enrollment_status='completed'
    ).first()
    
    if not enrollment:
        messages.error(request, 'You must complete the course before reviewing it.')
        return redirect('core:course_detail', course_slug=course_slug)
    
    # Check if already reviewed
    existing_review = CourseReview.objects.filter(
        student=student,
        course=course
    ).first()
    
    if request.method == 'POST':
        form = CourseReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.student = student
            review.course = course
            review.enrollment = enrollment
            review.is_verified = True
            review.is_published = True
            review.save()
            
            messages.success(request, 'Thank you for your review!')
            return redirect('core:course_detail', course_slug=course_slug)
    else:
        form = CourseReviewForm(instance=existing_review)
    
    context = {
        'course': course,
        'form': form,
        'existing_review': existing_review,
        'title': f'Review {course.name}'
    }
    return render(request, 'reviews/submit_review.html', context)

# ==================== CERTIFICATE VIEWS ====================
@login_required
def download_certificate(request, certificate_id):
    """Download certificate"""
    certificate = get_object_or_404(Certificate, id=certificate_id, student__user=request.user)
    
    # Increment download count
    certificate.downloaded_count += 1
    certificate.save()
    
    # Generate PDF (you need to implement this)
    # For now, return a simple HTML page
    context = {
        'certificate': certificate,
        'title': f'Certificate - {certificate.course_name}'
    }
    return render(request, 'certificates/certificate_pdf.html', context)

def verify_certificate(request, verification_code):
    """Verify certificate"""
    certificate = get_object_or_404(Certificate, verification_code=verification_code, is_verified=True)
    
    context = {
        'certificate': certificate,
        'title': 'Verify Certificate'
    }
    return render(request, 'certificates/verify.html', context)

# ==================== ERROR HANDLERS ====================
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