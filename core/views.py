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
from django.db.models import Prefetch
import uuid
# Add to views.py
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from decimal import Decimal
from .models import *
from .forms import *
from django.contrib.auth.decorators import user_passes_test
import random
import string
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required



def home(request):
    """Home page view"""
    # Featured courses
    featured_courses = Course.objects.filter(
        is_active=True,
        is_approved=True,
        is_featured=True
    ).order_by('-created_at')[:8]
    
    # Popular courses (by enrollments)
    popular_courses = Course.objects.filter(
        is_active=True,
        is_approved=True
    ).annotate(
        enroll_count=Count('enrollments')
    ).order_by('-enroll_count')[:8]
    
    # New courses
    new_courses = Course.objects.filter(
        is_active=True,
        is_approved=True,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:6]
    
    # Top instructors
    top_instructors = Instructor.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('instructor_courses', filter=Q(instructor_courses__course__is_active=True))
    ).filter(course_count__gt=0).order_by('-course_count')[:4]
    
    # Latest blog posts
    latest_posts = BlogPost.objects.filter(
        is_published=True
    ).order_by('-published_at', '-created_at')[:3]
    
    # Testimonials
    testimonials = CourseReview.objects.filter(
        is_published=True,
        rating__gte=4
    ).select_related('student', 'course').order_by('-created_at')[:4]
    
    # Categories
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True, courses__is_approved=True))
    ).filter(course_count__gt=0).order_by('-display_order', 'name')[:8]
    
    context = {
        'featured_courses': featured_courses,
        'popular_courses': popular_courses,
        'new_courses': new_courses,
        'top_instructors': top_instructors,
        'latest_posts': latest_posts,
        'testimonials': testimonials,
        'categories': categories,
        'page_title': 'Home - Islamic Online Learning Platform',
    }
    
    return render(request, 'core/home.html', context)

def course_list(request):
    """List all courses with filtering"""
    courses = Course.objects.filter(
        is_active=True,
        is_approved=True
    ).select_related('category')
    
    # Apply filters
    category_slug = request.GET.get('category', '')
    level = request.GET.get('level', '')
    price = request.GET.get('price', '')
    rating = request.GET.get('rating', '')
    search = request.GET.get('q', '')
    sort = request.GET.get('sort', 'newest')
    
    # Search filter
    if search:
        courses = courses.filter(
            Q(name__icontains=search) |
            Q(short_description__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search)
        )
    
    # Category filter
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    
    # Level filter
    if level:
        courses = courses.filter(level=level)
    
    # Price filter
    if price == 'free':
        courses = courses.filter(price_type='free')
    elif price == 'paid':
        courses = courses.filter(price_type__in=['paid', 'subscription'])
    
    # Rating filter
    if rating:
        try:
            min_rating = float(rating)
            courses = courses.filter(average_rating__gte=min_rating)
        except:
            pass
    
    # Sorting
    if sort == 'popular':
        courses = courses.order_by('-total_enrollments', '-average_rating')
    elif sort == 'rating':
        courses = courses.order_by('-average_rating', '-total_enrollments')
    elif sort == 'price_low':
        courses = courses.order_by('base_price')
    elif sort == 'price_high':
        courses = courses.order_by('-base_price')
    elif sort == 'featured':
        courses = courses.filter(is_featured=True).order_by('-created_at')
    else:  # newest
        courses = courses.order_by('-created_at')
    
    # Get categories for filter sidebar
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True))
    ).filter(course_count__gt=0).order_by('display_order', 'name')
    
    # Pagination
    paginator = Paginator(courses, 12)
    page = request.GET.get('page', 1)
    courses_page = paginator.get_page(page)
    
    context = {
        'courses': courses_page,
        'categories': categories,
        'selected_category': category_slug,
        'selected_level': level,
        'selected_price': price,
        'selected_rating': rating,
        'selected_sort': sort,
        'search_query': search,
        'page_title': 'Browse Courses',
    }
    
    return render(request, 'courses/browse.html', context)

def courses(request):
    """Browse all courses with filtering"""
    # Get all active courses
    courses_list = Course.objects.filter(
        is_active=True,
        is_approved=True
    ).select_related('category').prefetch_related('course_instructors__instructor')
    
    # Get filter parameters
    category_slug = request.GET.get('category', '')
    level = request.GET.get('level', '')
    price_type = request.GET.get('price', '')
    rating = request.GET.get('rating', '')
    search_query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', 'newest')
    
    # Apply search filter
    if search_query:
        courses_list = courses_list.filter(
            Q(name__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Apply category filter
    if category_slug:
        courses_list = courses_list.filter(category__slug=category_slug)
    
    # Apply level filter
    if level:
        courses_list = courses_list.filter(level=level)
    
    # Apply price filter
    if price_type == 'free':
        courses_list = courses_list.filter(price_type='free')
    elif price_type == 'paid':
        courses_list = courses_list.filter(price_type__in=['paid', 'subscription'])
    
    # Apply rating filter
    if rating:
        try:
            min_rating = float(rating)
            courses_list = courses_list.filter(average_rating__gte=min_rating)
        except:
            pass
    
    # Apply sorting
    if sort_by == 'popular':
        courses_list = courses_list.order_by('-total_enrollments', '-average_rating')
    elif sort_by == 'rating':
        courses_list = courses_list.order_by('-average_rating', '-total_enrollments')
    elif sort_by == 'price_low':
        courses_list = courses_list.order_by('base_price', '-average_rating')
    elif sort_by == 'price_high':
        courses_list = courses_list.order_by('-base_price', '-average_rating')
    elif sort_by == 'featured':
        courses_list = courses_list.filter(is_featured=True).order_by('-created_at')
    else:  # newest
        courses_list = courses_list.order_by('-created_at')
    
    # Get all categories for filter sidebar
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('courses', filter=Q(courses__is_active=True, courses__is_approved=True))
    ).filter(course_count__gt=0).order_by('display_order', 'name')
    
    # Get selected category
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    # Pagination
    paginator = Paginator(courses_list, 12)  # 12 courses per page
    page_number = request.GET.get('page', 1)
    courses_page = paginator.get_page(page_number)
    
    # Get filter counts for sidebar
    free_courses_count = Course.objects.filter(
        is_active=True, is_approved=True, price_type='free'
    ).count()
    paid_courses_count = Course.objects.filter(
        is_active=True, is_approved=True, price_type__in=['paid', 'subscription']
    ).count()
    
    # Get level counts
    level_counts = {
        'beginner': Course.objects.filter(is_active=True, is_approved=True, level='beginner').count(),
        'intermediate': Course.objects.filter(is_active=True, is_approved=True, level='intermediate').count(),
        'advanced': Course.objects.filter(is_active=True, is_approved=True, level='advanced').count(),
        'all': Course.objects.filter(is_active=True, is_approved=True, level='all').count(),
    }
    
    # Get rating counts
    rating_counts = {}
    for i in range(1, 6):
        rating_counts[str(i)] = Course.objects.filter(
            is_active=True, is_approved=True, average_rating__gte=i
        ).count()
    
    context = {
        'courses': courses_page,
        'categories': categories,
        'selected_category': selected_category,
        'selected_level': level,
        'selected_price': price_type,
        'selected_rating': rating,
        'selected_sort': sort_by,
        'search_query': search_query,
        'free_courses_count': free_courses_count,
        'paid_courses_count': paid_courses_count,
        'level_counts': level_counts,
        'rating_counts': rating_counts,
        'title': 'Browse All Courses',
        'total_courses': courses_list.count(),
    }
    
    return render(request, 'courses/browse.html', context)




def course_detail(request, slug):
    """Course detail page"""
    course = get_object_or_404(
        Course.objects.select_related('category')
                     .prefetch_related('modules', 'course_instructors__instructor'),
        slug=slug,
        is_active=True,
        is_approved=True
    )
    
    # Get related courses
    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True,
        is_approved=True
    ).exclude(id=course.id).order_by('-created_at')[:4]
    
    # Get reviews
    reviews = CourseReview.objects.filter(
        course=course,
        is_published=True
    ).select_related('student').order_by('-created_at')
    
    # Check enrollment status
    is_enrolled = False
    enrollment_status = None
    payment_status = None
    
    if request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        enrollment = Enrollment.objects.filter(
            student=request.user.student_profile,
            course=course
        ).first()
        
        if enrollment:
            is_enrolled = True
            enrollment_status = enrollment.enrollment_status
            payment_status = enrollment.payment_status
    
    # Check for coupon in URL
    coupon_code = request.GET.get('coupon', '')
    coupon_valid = False
    discount_amount = Decimal('0.00')
    final_price = course.get_current_price()
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            is_valid, message = coupon.is_valid(request.user, course)
            if is_valid:
                coupon_valid = True
                discount_amount = coupon.calculate_discount(course.get_current_price())
                final_price = course.get_current_price() - discount_amount
        except Coupon.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'related_courses': related_courses,
        'reviews': reviews,
        'is_enrolled': is_enrolled,
        'enrollment_status': enrollment_status,
        'payment_status': payment_status,
        'coupon_code': coupon_code,
        'coupon_valid': coupon_valid,
        'discount_amount': discount_amount,
        'final_price': final_price,
        'page_title': f'{course.name} - Course Details',
    }
    
    return render(request, 'courses/detail.html', context)


@login_required
def enroll_course(request, slug):
    """Enroll a student in a course"""
    course = get_object_or_404(Course, slug=slug, is_active=True, is_approved=True)
    student = request.user.student_profile
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        course=course
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.enrollment_status == 'active':
            messages.info(request, f'You are already enrolled in "{course.name}"')
            return redirect('core:course_learn', slug=slug)
        else:
            # Reactivate enrollment
            existing_enrollment.enrollment_status = 'active'
            existing_enrollment.save()
            messages.success(request, f'Re-enrolled in "{course.name}"')
            return redirect('core:course_learn', slug=slug)
    
    # Create new enrollment
    enrollment = Enrollment.objects.create(
        student=student,
        course=course,
        enrollment_status='pending',  # Will be active after payment if needed
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timezone.timedelta(days=course.access_duration_days)
    )
    
    # Handle payment for paid courses
    if course.price_type != 'free' and course.get_current_price() > 0:
        # Create pending payment
        payment = Payment.objects.create(
            enrollment=enrollment,
            student=student,
            amount=course.get_current_price(),
            payment_method='pending',
            transaction_id=f"ENR-{enrollment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
            status='pending'
        )
        
        messages.info(request, f'Please complete payment to enroll in "{course.name}"')
        return redirect('core:payment_process', payment_id=payment.id)
    
    # For free courses, activate immediately
    enrollment.enrollment_status = 'active'
    enrollment.payment_status = 'paid'
    enrollment.save()
    
    # Update student statistics
    student.total_courses_enrolled = student.enrollments.count()
    student.save()
    
    # Update course statistics
    course.total_enrollments += 1
    course.save()
    
    messages.success(request, f'Successfully enrolled in "{course.name}"!')
    return redirect('core:course_learn', slug=slug)

@login_required
def course_learn(request, slug):
    """Course learning page"""
    course = get_object_or_404(Course, slug=slug, is_active=True, is_approved=True)
    student = request.user.student_profile
    
    # Check if enrolled
    enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        enrollment_status='active'
    ).first()
    
    if not enrollment:
        messages.warning(request, 'You need to enroll in this course first')
        return redirect('core:course_detail', slug=slug)
    
    # Get first module and lesson
    first_module = course.modules.filter(is_published=True).order_by('order').first()
    first_lesson = None
    if first_module:
        first_lesson = first_module.lessons.filter(is_published=True).order_by('order').first()
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'first_module': first_module,
        'first_lesson': first_lesson,
        'page_title': f'Learning: {course.name}',
    }
    
    return render(request, 'courses/learn.html', context)

@login_required
def payment_process(request, payment_id):
    """Payment processing page"""
    payment = get_object_or_404(Payment, id=payment_id, student=request.user.student_profile)
    
    if request.method == 'POST':
        # Process payment (simplified)
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')
        
        if payment_method and transaction_id:
            payment.payment_method = payment_method
            payment.gateway_transaction_id = transaction_id
            payment.status = 'completed'
            payment.is_verified = True
            payment.verified_at = timezone.now()
            payment.save()
            
            # Update enrollment
            payment.enrollment.enrollment_status = 'active'
            payment.enrollment.payment_status = 'paid'
            payment.enrollment.save()
            
            messages.success(request, 'Payment successful! You are now enrolled in the course.')
            return redirect('core:course_learn', slug=payment.enrollment.course.slug)
    
    context = {
        'payment': payment,
        'page_title': 'Complete Payment',
    }
    
    return render(request, 'courses/payment.html', context)

def instructor_list(request):
    """List all instructors"""
    instructors = Instructor.objects.filter(
        is_active=True
    ).annotate(
        course_count=Count('instructor_courses', filter=Q(instructor_courses__course__is_active=True))
    ).order_by('-course_count')
    
    # Pagination
    paginator = Paginator(instructors, 12)
    page = request.GET.get('page', 1)
    instructors_page = paginator.get_page(page)
    
    context = {
        'instructors': instructors_page,
        'page_title': 'Our Instructors',
    }
    
    return render(request, 'instructors/list.html', context)

def blog_list(request):
    """List all blog posts"""
    posts = BlogPost.objects.filter(
        is_published=True
    ).order_by('-published_at', '-created_at')
    
    # Categories for filter
    categories = BlogPost.objects.filter(
        is_published=True
    ).values_list('category', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(posts, 9)
    page = request.GET.get('page', 1)
    posts_page = paginator.get_page(page)
    
    context = {
        'posts': posts_page,
        'categories': categories,
        'page_title': 'Islamic Blog & Articles',
    }
    
    return render(request, 'blog/list.html', context)

def blog_detail(request, slug):
    """Blog post detail"""
    post = get_object_or_404(
        BlogPost.objects.select_related('author'),
        slug=slug,
        is_published=True
    )
    
    # Increment views
    post.views += 1
    post.save()
    
    # Related posts
    related_posts = BlogPost.objects.filter(
        category=post.category,
        is_published=True
    ).exclude(id=post.id).order_by('-published_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'page_title': post.title,
    }
    
    return render(request, 'blog/detail.html', context)


def search(request):
    """Search courses, blog posts, and instructors"""
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'courses')
    
    results = {
        'courses': [],
        'blog_posts': [],
        'instructors': [],
        'total_results': 0,
    }
    
    if query:
        # Search courses
        if search_type in ['courses', 'all']:
            courses = Course.objects.filter(
                Q(name__icontains=query) |
                Q(short_description__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(course_instructors__instructor__full_name__icontains=query),
                is_active=True,
                is_approved=True
            ).distinct().select_related('category').order_by('-created_at')
            results['courses'] = courses
        
        # Search blog posts
        if search_type in ['blog', 'all']:
            blog_posts = BlogPost.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query),
                is_published=True
            ).distinct().order_by('-published_at')
            results['blog_posts'] = blog_posts
        
        # Search instructors
        if search_type in ['instructors', 'all']:
            instructors = Instructor.objects.filter(
                Q(full_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(specialization__icontains=query) |
                Q(qualifications__icontains=query),
                is_active=True
            ).distinct().order_by('-created_at')
            results['instructors'] = instructors
        
        # Calculate total results
        results['total_results'] = (
            len(results['courses']) + 
            len(results['blog_posts']) + 
            len(results['instructors'])
        )
    
    # Pagination for courses
    courses_paginator = Paginator(results['courses'], 12)
    courses_page = request.GET.get('courses_page', 1)
    results['courses_page'] = courses_paginator.get_page(courses_page)
    
    # Pagination for blog posts
    blog_paginator = Paginator(results['blog_posts'], 9)
    blog_page = request.GET.get('blog_page', 1)
    results['blog_posts_page'] = blog_paginator.get_page(blog_page)
    
    # Pagination for instructors
    instructors_paginator = Paginator(results['instructors'], 12)
    instructors_page = request.GET.get('instructors_page', 1)
    results['instructors_page'] = instructors_paginator.get_page(instructors_page)
    
    # Get all categories for sidebar
    categories = Category.objects.filter(
        is_active=True
    ).annotate(
        course_count=models.Count('courses', filter=Q(courses__is_active=True))
    ).filter(course_count__gt=0).order_by('display_order', 'name')
    
    context = {
        'query': query,
        'search_type': search_type,
        'results': results,
        'categories': categories,
        'page_title': f'Search: {query}' if query else 'Search',
    }
    
    return render(request, 'core/search.html', context)


# ==================== PAYMENT & ENROLLMENT SYSTEM ====================

@login_required
def initiate_payment(request, slug):
    """Initiate payment process for a course"""
    course = get_object_or_404(
        Course.objects.select_related('category'),
        slug=slug,
        is_active=True,
        is_approved=True
    )
    
    # Check if user has student profile
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, 'Student profile not found. Please complete your profile.')
        return redirect('core:profile')
    
    student = request.user.student_profile
    
    # Check if already enrolled
    existing_enrollment = Enrollment.objects.filter(
        student=student,
        course=course
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.enrollment_status == 'active':
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('core:course_learn', slug=slug)
        elif existing_enrollment.payment_status == 'paid':
            messages.info(request, 'Payment already completed for this course.')
            return redirect('core:course_learn', slug=slug)
    
    # For free courses, enroll directly
    if course.is_free():
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={
                'enrollment_status': 'active',
                'payment_status': 'free',
                'start_date': timezone.now().date(),
                'end_date': timezone.now().date() + timezone.timedelta(days=course.access_duration_days),
                'amount_paid': 0
            }
        )
        
        if not created:
            enrollment.enrollment_status = 'active'
            enrollment.payment_status = 'free'
            enrollment.save()
        
        messages.success(request, f'Successfully enrolled in {course.name}!')
        return redirect('core:course_learn', slug=slug)
    
    # Check coupon from URL
    coupon_code = request.GET.get('coupon', '')
    coupon = None
    discount_amount = Decimal('0.00')
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            is_valid, message = coupon.is_valid(request.user, course)
            if is_valid:
                discount_amount = coupon.calculate_discount(course.get_current_price())
                messages.success(request, f'Coupon applied! Discount: ৳{discount_amount}')
            else:
                messages.warning(request, message)
                coupon = None
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
    
    # Calculate final price
    original_price = course.get_current_price()
    final_price = original_price - discount_amount
    
    # Create or get enrollment
    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        course=course,
        defaults={
            'enrollment_status': 'pending',
            'payment_status': 'pending',
            'amount_paid': 0
        }
    )
    
    if not created and enrollment.payment_status == 'paid':
        messages.info(request, 'Payment already completed.')
        return redirect('core:course_learn', slug=slug)
    
    # Create payment record
    payment = Payment.objects.create(
        enrollment=enrollment,
        student=student,
        amount=final_price,
        payment_method='pending',
        transaction_id=f'PAY-{uuid.uuid4().hex[:12].upper()}',
        status='pending',
        gateway_response={
            'original_price': float(original_price),
            'discount_amount': float(discount_amount),
            'coupon_code': coupon_code if coupon else '',
            'course_slug': slug
        }
    )
    
    # Store payment ID in session for redirect
    request.session['current_payment_id'] = str(payment.id)
    
    return redirect('core:payment_method_selection', payment_id=payment.id)

@login_required
def payment_method_selection(request, payment_id):
    """Select payment method"""
    payment = get_object_or_404(
        Payment.objects.select_related('enrollment__course', 'student'),
        id=payment_id,
        student=request.user.student_profile
    )
    
    # Check if payment is already completed
    if payment.status == 'completed':
        messages.info(request, 'Payment already completed.')
        return redirect('core:course_learn', slug=payment.enrollment.course.slug)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method:
            payment.payment_method = payment_method
            payment.save()
            return redirect('core:payment_instructions', payment_id=payment.id)
    
    context = {
        'payment': payment,
        'page_title': 'Select Payment Method',
    }
    
    return render(request, 'payment/method_selection.html', context)

@login_required
def payment_instructions(request, payment_id):
    """Show payment instructions based on selected method"""
    payment = get_object_or_404(
        Payment.objects.select_related('enrollment__course', 'student'),
        id=payment_id,
        student=request.user.student_profile
    )
    
    # Generate instructions based on payment method
    payment_details = get_payment_instructions(payment)
    
    context = {
        'payment': payment,
        'payment_details': payment_details,
        'page_title': 'Payment Instructions',
    }
    
    return render(request, 'payment/instructions.html', context)

def get_payment_instructions(payment):
    """Generate payment instructions based on method"""
    if payment.payment_method == 'bkash':
        return {
            'method_name': 'bKash',
            'icon': 'fas fa-mobile-alt',
            'icon_color': '#E2136E',
            'account_number': '01740433580',
            'account_name': 'Taw Haa Zin Nurain Madarasa',
            'amount': payment.amount,
            'reference': payment.transaction_id,
            'instructions': [
                'Go to your bKash mobile menu',
                'Choose "Send Money"',
                f'Enter bKash Account: 01740433580',
                f'Enter Amount: ৳{payment.amount}',
                f'Enter Reference: {payment.transaction_id}',
                'Enter your bKash PIN',
                'Take screenshot of confirmation',
                'Click "Verify Payment" below'
            ]
        }
    elif payment.payment_method == 'nagad':
        return {
            'method_name': 'Nagad',
            'icon': 'fas fa-wallet',
            'icon_color': '#F8A61F',
            'account_number': '01740433580',
            'account_name': 'Taw Haa Zin Nurain Madarasa',
            'amount': payment.amount,
            'reference': payment.transaction_id,
            'instructions': [
                'Go to your Nagad mobile menu',
                'Choose "Send Money"',
                f'Enter Nagad Account: 01740433580',
                f'Enter Amount: ৳{payment.amount}',
                f'Enter Reference: {payment.transaction_id}',
                'Enter your Nagad PIN',
                'Take screenshot of confirmation',
                'Click "Verify Payment" below'
            ]
        }
    elif payment.payment_method == 'bank':
        return {
            'method_name': 'Bank Transfer',
            'icon': 'fas fa-university',
            'icon_color': '#27ae60',
            'account_number': '1234567890123',
            'account_name': 'Taw Haa Zin Nurain Online Madarasa',
            'bank_name': 'Islami Bank Bangladesh Ltd',
            'branch': 'Gulshan Branch, Dhaka',
            'amount': payment.amount,
            'reference': payment.transaction_id,
            'instructions': [
                f'Bank: Islami Bank Bangladesh Ltd',
                f'Account Name: Taw Haa Zin Nurain Online Madarasa',
                f'Account Number: 1234567890123',
                f'Branch: Gulshan Branch, Dhaka',
                f'Transfer Amount: ৳{payment.amount}',
                f'Reference: {payment.transaction_id}',
                'Upload transfer receipt below'
            ]
        }
    elif payment.payment_method == 'rocket':
        return {
            'method_name': 'Rocket',
            'icon': 'fas fa-bolt',
            'icon_color': '#5D2C8E',
            'account_number': '017404335801',
            'account_name': 'Taw Haa Zin Nurain Madarasa',
            'amount': payment.amount,
            'reference': payment.transaction_id,
            'instructions': [
                'Go to your Rocket/DBBL mobile menu',
                'Choose "Send Money"',
                f'Enter Rocket Account: 017404335801',
                f'Enter Amount: ৳{payment.amount}',
                f'Enter Reference: {payment.transaction_id}',
                'Enter your Rocket PIN',
                'Take screenshot of confirmation',
                'Click "Verify Payment" below'
            ]
        }
    
    return None

@login_required
def payment_verification(request, payment_id):
    """Submit payment verification"""
    payment = get_object_or_404(
        Payment.objects.select_related('enrollment__course', 'student'),
        id=payment_id,
        student=request.user.student_profile
    )
    
    if payment.status == 'completed':
        messages.info(request, 'Payment already verified.')
        return redirect('core:course_learn', slug=payment.enrollment.course.slug)
    
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        if transaction_id:
            payment.gateway_transaction_id = transaction_id
            payment.notes = notes
            payment.status = 'processing'
            
            # Handle file upload if provided
            if 'screenshot' in request.FILES:
                screenshot = request.FILES['screenshot']
                # You'll need to add a screenshot field to Payment model
                # For now, store filename in notes
                payment.notes += f'\nScreenshot: {screenshot.name}'
            
            payment.save()
            
            # Send notification to admin
            try:
                send_mail(
                    subject=f'Payment Verification Required - {payment.transaction_id}',
                    message=f'''Student: {payment.student.full_name}
Course: {payment.enrollment.course.name}
Amount: ৳{payment.amount}
Transaction ID: {transaction_id}
Payment Method: {payment.get_payment_method_display()}
Notes: {notes}

Please verify this payment in the admin panel.''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, 
                'Payment verification submitted! We will review it within 24 hours and activate your course.'
            )
            return redirect('core:dashboard')
    
    context = {
        'payment': payment,
        'page_title': 'Verify Payment',
    }
    
    return render(request, 'payment/verification.html', context)

@login_required
def payment_success(request, payment_id):
    """Payment success page"""
    payment = get_object_or_404(
        Payment.objects.select_related('enrollment__course', 'student'),
        id=payment_id,
        student=request.user.student_profile
    )
    
    context = {
        'payment': payment,
        'page_title': 'Payment Successful',
    }
    
    return render(request, 'payment/success.html', context)

@login_required
def check_payment_status(request, payment_id):
    """Check payment status (AJAX endpoint)"""
    if request.is_ajax() or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        payment = get_object_or_404(
            Payment,
            id=payment_id,
            student=request.user.student_profile
        )
        
        return JsonResponse({
            'status': payment.status,
            'is_verified': payment.is_verified,
            'enrollment_status': payment.enrollment.enrollment_status if payment.enrollment else 'pending'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# ==================== COURSE ENROLLMENT CHECK ====================

@login_required
def check_enrollment_status(request, slug):
    """Check if user is enrolled in a course (for AJAX calls)"""
    course = get_object_or_404(Course, slug=slug)
    
    if hasattr(request.user, 'student_profile'):
        enrollment = Enrollment.objects.filter(
            student=request.user.student_profile,
            course=course
        ).first()
        
        if enrollment:
            return JsonResponse({
                'enrolled': True,
                'status': enrollment.enrollment_status,
                'payment_status': enrollment.payment_status,
                'progress': enrollment.progress_percentage
            })
    
    return JsonResponse({'enrolled': False})
    

@login_required
def profile(request):
    """User profile page"""
    try:
        student_profile = request.user.student_profile
    except Student.DoesNotExist:
        # Create student profile if it doesn't exist
        student_profile = Student.objects.create(
            user=request.user,
            full_name=f"{request.user.first_name} {request.user.last_name}".strip()
            # Remove the email parameter as Student model doesn't have email field
        )
    
    # Get user's enrollments
    enrollments = Enrollment.objects.filter(
        student=student_profile
    ).select_related('course').order_by('-enrolled_at')
    
    # Get active courses (in progress)
    active_courses = enrollments.filter(
        enrollment_status='active'
    )[:5]
    
    # Get completed courses
    completed_courses = enrollments.filter(
        enrollment_status='completed'
    )[:5]
    
    # Get certificates
    certificates = Certificate.objects.filter(
        student=student_profile
    ).select_related('course').order_by('-issued_date')
    
    # Get course progress
    course_progress = StudentCourseProgress.objects.filter(
        student=student_profile
    ).select_related('course')
    
    # Calculate statistics
    total_enrollments = enrollments.count()
    completed_count = enrollments.filter(enrollment_status='completed').count()
    certificates_count = certificates.count()
    
    # Calculate total learning hours (estimate)
    total_learning_hours = 0
    for progress in course_progress:
        total_learning_hours += progress.total_time_spent // 60  # Convert minutes to hours
    
    context = {
        'student': student_profile,
        'user_form': UserUpdateForm(instance=request.user),
        'profile_form': StudentUpdateForm(instance=student_profile),
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'certificates': certificates[:3],
        'total_enrollments': total_enrollments,
        'completed_count': completed_count,
        'certificates_count': certificates_count,
        'total_learning_hours': total_learning_hours,
        'page_title': 'My Profile',
    }
    
    return render(request, 'profile/profile.html', context)



@login_required
def update_profile(request):
    """Update user profile"""
    student_profile = get_object_or_404(Student, user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = StudentUpdateForm(
            request.POST, 
            request.FILES, 
            instance=student_profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Update student's full name if user names changed
            if user_form.has_changed():
                student_profile.full_name = f"{user_form.cleaned_data['first_name']} {user_form.cleaned_data['last_name']}"
                student_profile.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = StudentUpdateForm(instance=student_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'student': student_profile,
        'page_title': 'Update Profile',
    }
    
    return render(request, 'profile/update_profile.html', context)


@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent logout
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('core:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'page_title': 'Change Password',
    }
    
    return render(request, 'profile/change_password.html', context)

    
# ==================== ADMIN DASHBOARD ====================

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    from django.db.models import Count, Sum
    
    # Get statistics
    total_courses = Course.objects.count()
    active_courses = Course.objects.filter(is_active=True).count()
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    total_instructors = Instructor.objects.count()
    active_instructors = Instructor.objects.filter(is_active=True).count()
    
    # Enrollment statistics
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(enrollment_status='active').count()
    completed_enrollments = Enrollment.objects.filter(enrollment_status='completed').count()
    
    # Payment statistics
    total_payments = Payment.objects.count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Recent activities
    recent_courses = Course.objects.order_by('-created_at')[:5]
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrolled_at')[:5]
    recent_payments = Payment.objects.select_related('student', 'enrollment__course').order_by('-payment_date')[:5]
    
    context = {
        'total_courses': total_courses,
        'active_courses': active_courses,
        'total_students': total_students,
        'active_students': active_students,
        'total_instructors': total_instructors,
        'active_instructors': active_instructors,
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'recent_courses': recent_courses,
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'page_title': 'Admin Dashboard',
    }
    
    return render(request, 'admin/dashboard.html', context)



def gallery(request):
    return HttpResponse("Gallery Page (Coming Soon)")

def faq(request):
    return HttpResponse("FAQ Page (Coming Soon)")

def donate(request):
    return HttpResponse("Donate Page (Coming Soon)")


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



   
    
    
    

# User Dashboard
# -------------------
def dashboard(request):
    return HttpResponse("User Dashboard (Coming Soon)")

def my_courses(request):
    return HttpResponse("My Courses Page (Coming Soon)")

def my_progress(request):
    return HttpResponse("My Progress Page (Coming Soon)")

def certificates(request):
    return HttpResponse("Certificates Page (Coming Soon)")

def payment_history(request):
    return HttpResponse("Payment History Page (Coming Soon)")

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