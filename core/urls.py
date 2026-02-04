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
    
    # Courses
    path('courses/', views.courses, name='courses'),
    # Authentication
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    # Search
    path('search/', views.search, name='search'),
    
    # User Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('my-progress/', views.my_progress, name='my_progress'),
    path('certificates/', views.certificates, name='certificates'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('instructors/', views.instructor_list, name='instructors'),

path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),


    # Resource URLs
    path('instructors/', views.instructor_list, name='instructors'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    
    path('gallery/', views.gallery, name='gallery'),
    path('faq/', views.faq, name='faq'),
    path('donate/', views.donate, name='donate'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),


    path('courses/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<slug:slug>/learn/', views.course_learn, name='course_learn'),
    path('payment/<uuid:payment_id>/', views.payment_process, name='payment_process'),
    
     path('course/<slug:slug>/enroll/', views.initiate_payment, name='initiate_payment'),
    path('payment/<uuid:payment_id>/method/', views.payment_method_selection, name='payment_method_selection'),
    path('payment/<uuid:payment_id>/instructions/', views.payment_instructions, name='payment_instructions'),
    path('payment/<uuid:payment_id>/verify/', views.payment_verification, name='payment_verification'),
    path('payment/<uuid:payment_id>/success/', views.payment_success, name='payment_success'),
    path('payment/<uuid:payment_id>/status/', views.check_payment_status, name='check_payment_status'),
    path('course/<slug:slug>/enrollment-status/', views.check_enrollment_status, name='check_enrollment_status'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)