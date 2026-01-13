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
        'title': 'Our Courses - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'courses/course_list.html', context)

def course_detail(request, course_id):
    """Display course details"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True
    ).exclude(id=course.id)[:3]
    
    # Check if user is enrolled
    is_enrolled = False
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        is_enrolled = Enrollment.objects.filter(
            student=request.user.student_profile,
            course=course,
            enrollment_status__in=['active', 'completed']
        ).exists()
    
    context = {
        'course': course,
        'related_courses': related_courses,
        'is_enrolled': is_enrolled,
        'title': f'{course.name} - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def enroll_course(request, course_id):
    """Enroll in a course"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Please complete your student profile first.')
        return redirect('core:profile_settings')
    
    student = request.user.student_profile
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        enrollment_status__in=['active', 'pending']
    ).first()
    
    if existing_enrollment:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_detail', course_id=course_id)
    
    # Check course availability
    if course.current_enrollment >= course.max_students:
        messages.error(request, 'This course is currently full. Please try another course or check back later.')
        return redirect('course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.course = course
            enrollment.course_fee = course.base_fee
            enrollment.due_amount = course.base_fee
            
            # Check if discount applies
            if course.discount_fee:
                enrollment.course_fee = course.discount_fee
                enrollment.discount_applied = course.base_fee - course.discount_fee
                enrollment.due_amount = course.discount_fee
            
            enrollment.save()
            
            # Update course enrollment count
            course.current_enrollment += 1
            course.save()
            
            messages.success(request, f'Successfully enrolled in {course.name}! Please complete payment to start classes.')
            return redirect('make_payment', enrollment_id=enrollment.id)
    else:
        form = EnrollmentForm(initial={
            'class_time_slot': student.preferred_time_slot,
        })
    
    context = {
        'course': course,
        'form': form,
        'title': f'Enroll in {course.name}',
    }
    return render(request, 'courses/enroll.html', context)

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
    
    context = {
        'payments': payments,
        'total_paid': payments.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0,
        'total_due': enrollments.filter(payment_status__in=['pending', 'partial']).aggregate(Sum('due_amount'))['due_amount__sum'] or 0,
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
            return redirect('payment_success', transaction_id=payment.transaction_id)
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



# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserUpdateForm, StudentUpdateForm, StudentRegistrationForm

@login_required
def profile_settings(request):
    """User profile settings"""
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
                else:
                    student = student_form.save(commit=False)
                    student.user = request.user
                    # Generate student ID
                    import uuid
                    student.student_id = f"STU-{uuid.uuid4().hex[:8].upper()}"
                    student.save()
                    messages.success(request, 'Student profile created successfully!')
                
                messages.success(request, 'Profile updated successfully!')
                return redirect('core:profile_settings')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect('core:profile_settings')
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)
        
        if student:
            student_form = StudentUpdateForm(instance=student)
        else:
            student_form = StudentRegistrationForm()
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'password_form': password_form,
        'student': student,
        'title': 'Profile Settings - Taw Haa Zin Nurain Online Madarasa',
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
    return render(request, 'core:about.html', context)

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

