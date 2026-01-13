from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    
    # Courses
    path('courses/', views.courses, name='courses'),
    path('courses/<uuid:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<uuid:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    
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
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/my-courses/', views.my_courses, name='my_courses'),
    path('dashboard/my-progress/', views.my_progress, name='my_progress'),
    path('dashboard/payment-history/', views.payment_history, name='payment_history'),
    path('dashboard/make-payment/<uuid:enrollment_id>/', views.make_payment, name='make_payment'),
    path('dashboard/payment-success/<str:transaction_id>/', views.payment_success, name='payment_success'),
    path('dashboard/certificates/', views.certificates, name='certificates'),
    path('dashboard/certificates/<uuid:enrollment_id>/download/', views.download_certificate, name='download_certificate'),
    path('dashboard/schedule/', views.schedule, name='schedule'),
    path('dashboard/profile-settings/', views.profile_settings, name='profile_settings'),
    
    path('dashboard/student/<int:student_id>/', views.student_profile, name='student_profile'),

    
    # API Endpoints
    path('api/dashboard-stats/', views.get_dashboard_stats, name='dashboard_stats'),
    path('api/check-payment-reminders/', views.check_payment_reminders, name='check_payment_reminders'),
    path('api/update-progress/', views.update_progress, name='update_progress'),
]