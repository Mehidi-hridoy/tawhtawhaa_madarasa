from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .logindetails import register, user_login, user_logout

app_name = 'core'

urlpatterns = [
    # Home & Public
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    
    # Courses
    path('courses/', views.courses, name='courses'),
    path('courses/<slug:course_slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:course_slug>/enroll/', views.enroll_course, name='enroll_course'),
    
    # Learning Dashboard
    path('learning/<uuid:enrollment_id>/', views.learning_dashboard, name='learning_dashboard'),
    path('learning/<uuid:enrollment_id>/lesson/<uuid:lesson_id>/', views.lesson_view, name='lesson_view'),
    
    # Quiz
    path('learning/<uuid:enrollment_id>/quiz/<uuid:quiz_id>/', views.start_quiz, name='start_quiz'),
    path('api/submit-quiz/<uuid:attempt_id>/', views.submit_quiz, name='submit_quiz'),
    
    # API Views
    path('api/submit-mcq/', views.submit_mcq_response, name='submit_mcq'),
    path('api/complete-lesson/<uuid:lesson_id>/', views.complete_lesson, name='complete_lesson'),
    path('api/save-video-progress/', views.save_video_progress, name='save_video_progress'),
    
    # Team
    path('team/', views.team, name='team'),
    path('team/<uuid:instructor_id>/', views.instructor_detail, name='instructor_detail'),
    
    # Blog
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    
    # Gallery
    path('gallery/', views.gallery, name='gallery'),
    
    # FAQ
    path('faq/', views.faq, name='faq'),
    
    # Donation
    path('donate/', views.donate, name='donate'),
    path('donate/success/<str:transaction_id>/', views.donation_success, name='donation_success'),
    
    # Authentication
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/my-courses/', views.my_courses, name='my_courses'),
    path('dashboard/my-progress/', views.my_progress, name='my_progress'),
    path('dashboard/payment-history/', views.payment_history, name='payment_history'),
    path('dashboard/certificates/', views.certificates, name='certificates'),
    path('dashboard/profile-settings/', views.profile_settings, name='profile_settings'),
    
    # Payment & Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('payment/success/<str:transaction_id>/', views.payment_success, name='payment_success'),
    
    # Wishlist
    path('wishlist/', views.wishlist, name='wishlist'),
    path('api/add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('api/remove-from-wishlist/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    # Reviews
    path('courses/<slug:course_slug>/review/', views.submit_review, name='submit_review'),
    
    # Certificates
    path('certificates/download/<uuid:certificate_id>/', views.download_certificate, name='download_certificate'),
    path('verify-certificate/<str:verification_code>/', views.verify_certificate, name='verify_certificate'),
    
    # API Endpoints
    path('api/dashboard-stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('api/check-payment-reminders/', views.check_payment_reminders, name='check_payment_reminders'),
    path('api/update-progress/', views.update_progress, name='update_progress'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)