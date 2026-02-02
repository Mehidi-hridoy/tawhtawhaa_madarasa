# create_test_data.py - Save this in your app's management/commands folder
# Run with: python manage.py create_test_data

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tawhtawhaa_madarasa.settings')

import django
django.setup()

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from decimal import Decimal
import uuid
from django.utils import timezone
import random
from datetime import timedelta
import json

class Command(BaseCommand):
    help = 'Create comprehensive test data with 20 Islamic courses and all related models'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('CREATING COMPREHENSIVE TEST DATA FOR ISLAMIC MADRASSA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        self.create_users()
        self.create_categories()
        self.create_20_courses()
        self.create_coupons()
        self.create_enrollments_and_progress()
        self.create_learning_data()
        self.create_blog_posts()
        self.create_faq()
        self.create_resources()
        self.create_reviews()
        self.create_certificates()
        self.create_gallery()
        self.create_donations()
        
        self.print_summary()
    
    def create_users(self):
        """Create admin, instructors, and students"""
        self.stdout.write(self.style.SUCCESS('\n1. CREATING USERS'))
        
        # Admin user
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@tawhaazin.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Admin created: {admin.username}'))
        
        # Create 3 instructors
        instructors_data = [
            {
                'username': 'instructor1',
                'email': 'instructor1@tawhaazin.com',
                'full_name': 'Dr. Muhammad Abdullah',
                'title': 'Senior Islamic Scholar',
                'specialization': 'Quranic Sciences, Tafsir',
                'role': 'lead'
            },
            {
                'username': 'instructor2',
                'email': 'instructor2@tawhaazin.com',
                'full_name': 'Shaykh Abdul Karim',
                'title': 'Hadith Specialist',
                'specialization': 'Hadith Sciences, Seerah',
                'role': 'senior'
            },
            {
                'username': 'instructor3',
                'email': 'instructor3@tawhaazin.com',
                'full_name': 'Ustadha Fatima Begum',
                'title': 'Female Education Specialist',
                'specialization': 'Fiqh for Women, Islamic Etiquette',
                'role': 'senior'
            }
        ]
        
        self.instructors = []
        for data in instructors_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['full_name'].split()[0],
                    'last_name': ' '.join(data['full_name'].split()[1:]),
                    'password': 'instructor123'
                }
            )
            
            instructor, created = Instructor.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': data['full_name'],
                    'title': data['title'],
                    'bio': f'{data["title"]} with extensive knowledge in {data["specialization"]}. Graduated from Islamic University of Madinah with 15+ years of teaching experience.',
                    'specialization': data['specialization'],
                    'role': data['role'],
                    'experience_years': random.randint(10, 25),
                    'qualifications': 'M.A. in Islamic Studies, Ijazah in multiple fields',
                    'phone': f'+88017{random.randint(1000000, 9999999)}',
                    'email': data['email'],
                    'is_active': True,
                    'is_verified': True
                }
            )
            self.instructors.append(instructor)
            self.stdout.write(self.style.SUCCESS(f'✓ Instructor created: {instructor.full_name}'))
        
        # Create 5 students
        self.students = []
        student_names = [
            'Abdullah Rahman', 'Fatima Akter', 'Mohammad Ali',
            'Aisha Begum', 'Ibrahim Hossain'
        ]
        
        for i, name in enumerate(student_names, 1):
            user, created = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'email': f'student{i}@tawhaazin.com',
                    'first_name': name.split()[0],
                    'last_name': ' '.join(name.split()[1:]),
                    'password': 'student123'
                }
            )
            
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': name,
                    'phone': f'+88018{random.randint(1000000, 9999999)}',
                    'gender': 'male' if i % 2 == 1 else 'female',
                    'occupation': random.choice(['student', 'professional', 'business', 'housewife']),
                    'education_level': random.choice(['High School', 'Bachelor', 'Master', 'PhD']),
                    'country': 'Bangladesh',
                    'city': random.choice(['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi']),
                    'is_active': True
                }
            )
            self.students.append(student)
            self.stdout.write(self.style.SUCCESS(f'✓ Student created: {student.full_name}'))
    
    def create_categories(self):
        """Create Islamic course categories"""
        self.stdout.write(self.style.SUCCESS('\n2. CREATING CATEGORIES'))
        
        categories_data = [
            {'name': 'Quran Recitation', 'color': '#1a5fb4', 'icon': 'fas fa-quran'},
            {'name': 'Quran Memorization (Hifz)', 'color': '#26a269', 'icon': 'fas fa-brain'},
            {'name': 'Tadabbur Quran', 'color': '#c64600', 'icon': 'fas fa-lightbulb'},
            {'name': 'Tafsir', 'color': '#9b59b6', 'icon': 'fas fa-book-open'},
            {'name': 'Seerah', 'color': '#e74c3c', 'icon': 'fas fa-mosque'},
            {'name': 'Hadith Studies', 'color': '#f39c12', 'icon': 'fas fa-quote-right'},
            {'name': 'Aqida & Tawheed', 'color': '#27ae60', 'icon': 'fas fa-star-of-david'},
            {'name': 'Fiqh (Islamic Jurisprudence)', 'color': '#8e44ad', 'icon': 'fas fa-balance-scale'},
            {'name': 'Arabic Language', 'color': '#16a085', 'icon': 'fas fa-language'},
            {'name': 'Islamic History', 'color': '#d35400', 'icon': 'fas fa-history'},
            {'name': 'Islamic Ethics & Manners', 'color': '#c0392b', 'icon': 'fas fa-hands-helping'},
            {'name': 'Contemporary Issues', 'color': '#2980b9', 'icon': 'fas fa-globe'},
        ]
        
        self.categories = {}
        for data in categories_data:
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': f'Learn authentic {data["name"].lower()} from qualified scholars',
                    'color': data['color'],
                    'icon_class': data['icon'],
                    'display_order': len(self.categories) + 1
                }
            )
            self.categories[data['name']] = category
            self.stdout.write(self.style.SUCCESS(f'✓ Category: {category.name}'))
    
    def create_20_courses(self):
        """Create 20 comprehensive Islamic courses"""
        self.stdout.write(self.style.SUCCESS('\n3. CREATING 20 ISLAMIC COURSES'))
        
        courses_data = [
            # Quran Courses
            {
                'name': 'Complete Tajweed Course - Level 1',
                'category': 'Quran Recitation',
                'price': 2000,
                'sale_price': 1500,
                'duration': 40,
                'level': 'beginner',
                'instructor_idx': 0,
                'featured': True
            },
            {
                'name': 'Advanced Tajweed & Qiraat',
                'category': 'Quran Recitation',
                'price': 3500,
                'duration': 60,
                'level': 'advanced',
                'instructor_idx': 0,
                'featured': True
            },
            {
                'name': 'Hifz Program - Juz Amma',
                'category': 'Quran Memorization (Hifz)',
                'price': 5000,
                'duration': 80,
                'level': 'beginner',
                'instructor_idx': 0,
                'featured': True
            },
            {
                'name': 'Complete Quran Memorization',
                'category': 'Quran Memorization (Hifz)',
                'price': 15000,
                'duration': 600,
                'level': 'all',
                'instructor_idx': 0,
                'featured': False
            },
            
            # Tadabbur & Tafsir
            {
                'name': 'Tadabbur of Surah Yasin',
                'category': 'Tadabbur Quran',
                'price': 2500,
                'sale_price': 1800,
                'duration': 45,
                'level': 'intermediate',
                'instructor_idx': 0,
                'featured': True
            },
            {
                'name': 'Tafsir Ibn Kathir - Selected Surahs',
                'category': 'Tafsir',
                'price': 4000,
                'duration': 70,
                'level': 'intermediate',
                'instructor_idx': 0,
                'featured': False
            },
            
            # Seerah & Hadith
            {
                'name': 'Seerah of Prophet Muhammad (PBUH)',
                'category': 'Seerah',
                'price': 0,
                'duration': 50,
                'level': 'beginner',
                'instructor_idx': 1,
                'featured': True
            },
            {
                'name': '40 Hadith of Imam Nawawi',
                'category': 'Hadith Studies',
                'price': 3000,
                'duration': 55,
                'level': 'beginner',
                'instructor_idx': 1,
                'featured': True
            },
            {
                'name': 'Riyad us-Saliheen Study',
                'category': 'Hadith Studies',
                'price': 4500,
                'duration': 75,
                'level': 'intermediate',
                'instructor_idx': 1,
                'featured': False
            },
            
            # Aqida & Fiqh
            {
                'name': 'Aqida Tahawiyyah Explained',
                'category': 'Aqida & Tawheed',
                'price': 3500,
                'sale_price': 2800,
                'duration': 60,
                'level': 'intermediate',
                'instructor_idx': 1,
                'featured': True
            },
            {
                'name': 'Fiqh of Salah & Taharah',
                'category': 'Fiqh (Islamic Jurisprudence)',
                'price': 2000,
                'duration': 40,
                'level': 'beginner',
                'instructor_idx': 1,
                'featured': False
            },
            {
                'name': 'Fiqh of Fasting & Zakat',
                'category': 'Fiqh (Islamic Jurisprudence)',
                'price': 2500,
                'duration': 45,
                'level': 'beginner',
                'instructor_idx': 1,
                'featured': False
            },
            
            # Arabic Language
            {
                'name': 'Arabic for Beginners - Level 1',
                'category': 'Arabic Language',
                'price': 4000,
                'sale_price': 3000,
                'duration': 80,
                'level': 'beginner',
                'instructor_idx': 0,
                'featured': True
            },
            {
                'name': 'Arabic Grammar & Morphology',
                'category': 'Arabic Language',
                'price': 5000,
                'duration': 90,
                'level': 'intermediate',
                'instructor_idx': 0,
                'featured': False
            },
            
            # Islamic History & Ethics
            {
                'name': 'Golden Age of Islam',
                'category': 'Islamic History',
                'price': 2800,
                'duration': 50,
                'level': 'intermediate',
                'instructor_idx': 1,
                'featured': False
            },
            {
                'name': 'Islamic Ethics & Character Building',
                'category': 'Islamic Ethics & Manners',
                'price': 2000,
                'duration': 35,
                'level': 'beginner',
                'instructor_idx': 2,
                'featured': True
            },
            
            # Contemporary Issues
            {
                'name': 'Islamic Finance & Banking',
                'category': 'Contemporary Issues',
                'price': 5000,
                'duration': 65,
                'level': 'advanced',
                'instructor_idx': 1,
                'featured': True
            },
            {
                'name': 'Muslim Family System',
                'category': 'Contemporary Issues',
                'price': 3000,
                'duration': 50,
                'level': 'intermediate',
                'instructor_idx': 2,
                'featured': False
            },
            
            # Special Courses
            {
                'name': 'Dua & Dhikr - Daily Supplications',
                'category': 'Islamic Ethics & Manners',
                'price': 1500,
                'duration': 30,
                'level': 'beginner',
                'instructor_idx': 2,
                'featured': False
            },
            {
                'name': 'Islamic Parenting Guide',
                'category': 'Contemporary Issues',
                'price': 3500,
                'duration': 55,
                'level': 'intermediate',
                'instructor_idx': 2,
                'featured': True
            },
        ]
        
        admin_user = User.objects.get(username='admin')
        self.courses = []
        
        for idx, data in enumerate(courses_data, 1):
            category = self.categories[data['category']]
            instructor = self.instructors[data['instructor_idx']]
            
            course = Course.objects.create(
                name=data['name'],
                slug=f"{slugify(data['name'])}-{idx}",
                category=category,
                description=self.generate_course_description(data['name'], data['level']),
                short_description=f"Learn authentic {data['name'].split('-')[0].strip()} from qualified scholars",
                course_type=random.choice(['self_paced', 'instructor_led', 'hybrid']),
                level=data['level'],
                price_type='free' if data['price'] == 0 else 'paid',
                base_price=Decimal(str(data['price'])),
                sale_price=Decimal(str(data['sale_price'])) if 'sale_price' in data else None,
                estimated_duration_hours=data['duration'],
                is_featured=data['featured'],
                is_active=True,
                is_approved=True,
                certificate_available=True,
                learning_outcomes=self.generate_learning_outcomes(data['name']),
                prerequisites=self.generate_prerequisites(data['level']),
                target_audience=self.generate_target_audience(data['level']),
                created_by=admin_user,
                published_at=timezone.now()
            )
            
            # Add instructor
            CourseInstructor.objects.create(
                course=course,
                instructor=instructor,
                is_primary=True,
                display_order=1
            )
            
            # Create modules and lessons
            self.create_course_content(course, data['duration'])
            
            self.courses.append(course)
            price_display = 'FREE' if data['price'] == 0 else f"৳{data['price']}"
            sale_display = f" (Sale: ৳{data['sale_price']})" if 'sale_price' in data else ""
            self.stdout.write(self.style.SUCCESS(
                f"{idx:2d}. {course.name} - {price_display}{sale_display}"
            ))
    
    def generate_course_description(self, name, level):
        """Generate realistic course description"""
        descriptions = {
            'beginner': f"This {level} level course provides comprehensive introduction to {name}. Perfect for those starting their Islamic learning journey.",
            'intermediate': f"Take your knowledge to the next level with this {level} course on {name}. Build upon basic concepts and develop deeper understanding.",
            'advanced': f"Advanced study of {name} for serious students. This course delves into complex topics and scholarly discussions.",
            'all': f"A comprehensive course on {name} suitable for students of all levels. From beginners to advanced learners."
        }
        return descriptions.get(level, descriptions['beginner'])
    
    def generate_learning_outcomes(self, course_name):
        """Generate learning outcomes based on course name"""
        outcomes = [
            "Understand core concepts and principles",
            "Apply knowledge in practical situations",
            "Develop critical thinking skills",
            "Gain confidence in the subject matter",
            "Prepare for advanced study",
            "Build strong foundation for lifelong learning",
            "Improve spiritual connection through knowledge"
        ]
        return "\n".join([f"{i+1}. {outcome}" for i, outcome in enumerate(random.sample(outcomes, 5))])
    
    def generate_prerequisites(self, level):
        """Generate prerequisites based on level"""
        if level == 'beginner':
            return "No prior knowledge required. Open to all Muslim brothers and sisters."
        elif level == 'intermediate':
            return "Basic understanding of Islamic concepts. Completion of beginner level courses recommended."
        else:
            return "Strong foundation in Islamic studies. Previous course completion required."
    
    def generate_target_audience(self, level):
        """Generate target audience description"""
        audiences = {
            'beginner': "New Muslims, beginners in Islamic studies, students seeking foundation knowledge",
            'intermediate': "Intermediate students, those who completed beginner courses, seekers of deeper knowledge",
            'advanced': "Advanced students, Islamic studies graduates, aspiring scholars",
            'all': "All Muslims seeking to increase their Islamic knowledge"
        }
        return audiences.get(level, audiences['all'])
    
    def create_course_content(self, course, total_duration):
        """Create modules, lessons, and quizzes for a course"""
        module_count = random.randint(4, 6)
        hours_per_module = total_duration // module_count
        
        for module_idx in range(1, module_count + 1):
            module = Module.objects.create(
                course=course,
                title=f"Module {module_idx}: {self.generate_module_title(course.name, module_idx)}",
                description=f"Comprehensive study module covering key aspects of {course.name.split('-')[0].strip()}",
                order=module_idx,
                duration_minutes=hours_per_module * 60,
                is_published=True
            )
            
            # Create 4-6 lessons per module
            lesson_count = random.randint(4, 6)
            for lesson_idx in range(1, lesson_count + 1):
                lesson_type = random.choice(['video', 'article', 'quiz'])
                lesson = Lesson.objects.create(
                    module=module,
                    title=f"Lesson {lesson_idx}: {self.generate_lesson_title(course.name, lesson_idx)}",
                    lesson_type=lesson_type,
                    description=f"Detailed lesson on {self.generate_lesson_title(course.name, lesson_idx).lower()}",
                    content=f"<p>Comprehensive content for {self.generate_lesson_title(course.name, lesson_idx)}. This lesson covers important concepts and practical applications.</p>" if lesson_type == 'article' else "",
                    order=lesson_idx,
                    duration_minutes=random.randint(20, 60),
                    is_published=True,
                    is_free=random.choice([True, False]),
                    require_completion=True,
                    points_value=random.randint(5, 20)
                )
                
                # Create quiz for some lessons
                if lesson_type == 'quiz':
                    quiz = Quiz.objects.create(
                        title=f"Quiz: {lesson.title}",
                        description=f"Assessment quiz for {lesson.title}",
                        quiz_type='module',
                        duration_minutes=30,
                        passing_score=70,
                        max_attempts=3,
                        show_correct_answers=True,
                        is_published=True,
                        is_active=True,
                        course=course,
                        module=module
                    )
                    
                    # Create 5-10 quiz questions
                    question_count = random.randint(5, 10)
                    for q_idx in range(1, question_count + 1):
                        question = QuizQuestion.objects.create(
                            quiz=quiz,
                            question_type='mcq_single',
                            question_text=f"What is the correct understanding of concept {q_idx} in {course.name.split('-')[0].strip()}?",
                            explanation=f"Detailed explanation for question {q_idx}",
                            points=100 // question_count,
                            order=q_idx,
                            is_active=True
                        )
                        
                        # Create 4 options
                        for opt_idx in range(1, 5):
                            QuestionOption.objects.create(
                                question=question,
                                option_text=f"Option {opt_idx}: {self.generate_option_text(course.name)}",
                                is_correct=(opt_idx == 1),  # First option is correct
                                order=opt_idx
                            )
    
    def generate_module_title(self, course_name, module_idx):
        """Generate module titles"""
        prefixes = ['Introduction to', 'Fundamentals of', 'Advanced Concepts in', 
                   'Practical Applications of', 'Case Studies in', 'Review of']
        topics = ['Core Principles', 'Key Concepts', 'Practical Implementation', 
                 'Common Issues', 'Best Practices', 'Future Trends']
        return f"{random.choice(prefixes)} {random.choice(topics)}"
    
    def generate_lesson_title(self, course_name, lesson_idx):
        """Generate lesson titles"""
        topics = [
            'Basic Concepts', 'Historical Background', 'Practical Examples',
            'Common Mistakes', 'Advanced Techniques', 'Review Session',
            'Case Studies', 'Interactive Discussion', 'Assessment Preparation'
        ]
        return random.choice(topics)
    
    def generate_option_text(self, course_name):
        """Generate quiz option text"""
        adjectives = ['correct', 'incorrect', 'partially correct', 'misunderstood']
        return f"A {random.choice(adjectives)} understanding of the concept"
    
    def create_coupons(self):
        """Create discount coupons"""
        self.stdout.write(self.style.SUCCESS('\n4. CREATING COUPONS'))
        
        coupons_data = [
            {
                'code': 'RAMADAN2024',
                'discount_type': 'percentage',
                'value': 20,
                'description': 'Ramadan Special Discount'
            },
            {
                'code': 'NEWSTUDENT',
                'discount_type': 'percentage',
                'value': 15,
                'description': 'Discount for new students'
            },
            {
                'code': 'HIFZ50',
                'discount_type': 'fixed',
                'value': 5000,
                'description': 'Special discount for Hifz program'
            },
            {
                'code': 'FREETRIAL',
                'discount_type': 'free',
                'value': 100,
                'description': 'Free trial for one course'
            },
        ]
        
        admin_user = User.objects.get(username='admin')
        valid_from = timezone.now()
        valid_until = valid_from + timedelta(days=365)
        
        self.coupons = []
        for data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=data['code'],
                defaults={
                    'discount_type': data['discount_type'],
                    'discount_value': data['value'],
                    'valid_from': valid_from,
                    'valid_until': valid_until,
                    'usage_limit': 100,
                    'minimum_cart_amount': Decimal('1000.00'),
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            # Assign coupons to some courses
            applicable_courses = random.sample(self.courses, random.randint(3, 8))
            coupon.applicable_courses.set(applicable_courses)
            
            self.coupons.append(coupon)
            self.stdout.write(self.style.SUCCESS(
                f'✓ Coupon: {coupon.code} ({coupon.discount_value}{"%" if coupon.discount_type == "percentage" else "৳"})'
            ))
    
    def create_enrollments_and_progress(self):
        """Create enrollments and progress for students"""
        self.stdout.write(self.style.SUCCESS('\n5. CREATING ENROLLMENTS & PROGRESS'))
        
        for student in self.students:
            # Enroll each student in 3-8 courses
            enroll_count = random.randint(3, 8)
            selected_courses = random.sample(self.courses, enroll_count)
            
            for course in selected_courses:
                # Determine enrollment status
                status_options = ['active', 'completed', 'pending', 'dropped']
                weights = [60, 20, 10, 10]
                status = random.choices(status_options, weights=weights)[0]
                
                # Create enrollment
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrollment_status=status,
                    payment_status='paid' if course.base_price > 0 else 'free',
                    amount_paid=course.get_current_price(),
                    start_date=timezone.now().date() - timedelta(days=random.randint(0, 180)),
                    progress_percentage=random.randint(0, 100) if status == 'active' else (100 if status == 'completed' else 0),
                    total_time_spent=random.randint(0, course.estimated_duration_hours * 60)
                )
                
                # Create payment record for paid courses
                if course.base_price > 0:
                    payment = Payment.objects.create(
                        enrollment=enrollment,
                        student=student,
                        amount=course.get_current_price(),
                        payment_method=random.choice(['bkash', 'nagad', 'rocket', 'bank']),
                        transaction_id=f"TX{random.randint(100000, 999999)}",
                        status='completed',
                        is_verified=True,
                        verified_at=timezone.now()
                    )
                
                # Create lesson progress for active/completed enrollments
                if status in ['active', 'completed']:
                    lessons = Lesson.objects.filter(module__course=course, is_published=True)
                    completed_count = int(len(lessons) * (enrollment.progress_percentage / 100))
                    
                    for i, lesson in enumerate(lessons[:completed_count]):
                        progress = StudentLessonProgress.objects.create(
                            student=student,
                            lesson=lesson,
                            enrollment=enrollment,
                            status='completed',
                            started_at=enrollment.start_date,
                            completed_at=enrollment.start_date + timedelta(days=i+1),
                            video_progress_seconds=lesson.duration_minutes * 60,
                            points_earned=lesson.points_value
                        )
                    
                    # Create progress for some remaining lessons
                    remaining_lessons = lessons[completed_count:completed_count + 3]
                    for lesson in remaining_lessons:
                        StudentLessonProgress.objects.create(
                            student=student,
                            lesson=lesson,
                            enrollment=enrollment,
                            status='in_progress',
                            started_at=timezone.now() - timedelta(days=random.randint(1, 7)),
                            video_progress_seconds=random.randint(0, lesson.duration_minutes * 30)
                        )
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ {student.full_name} enrolled in {enroll_count} courses'
            ))
    
    def create_learning_data(self):
        """Create additional learning data - quiz attempts, wishlist, etc."""
        self.stdout.write(self.style.SUCCESS('\n6. CREATING LEARNING DATA'))
        
        # Create wishlist items
        for student in self.students:
            wishlist_count = random.randint(2, 5)
            wishlist_courses = random.sample(self.courses, wishlist_count)
            
            for course in wishlist_courses:
                # Only add to wishlist if not already enrolled
                if not Enrollment.objects.filter(student=student, course=course).exists():
                    Wishlist.objects.get_or_create(
                        student=student,
                        course=course
                    )
            
            # Create quiz attempts
            enrollments = Enrollment.objects.filter(student=student, enrollment_status='active')
            for enrollment in enrollments[:2]:  # Create attempts for first 2 enrollments
                quizzes = Quiz.objects.filter(course=enrollment.course)
                for quiz in quizzes[:random.randint(1, 3)]:  # Attempt 1-3 quizzes
                    attempt = StudentQuizAttempt.objects.create(
                        student=student,
                        quiz=quiz,
                        enrollment=enrollment,
                        attempt_number=1,
                        submitted_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                        time_taken_seconds=random.randint(300, 1800),
                        score=random.randint(60, 95),
                        total_questions=quiz.questions.count(),
                        correct_answers=int(quiz.questions.count() * random.uniform(0.6, 0.95)),
                        is_completed=True,
                        is_passed=True
                    )
        
        self.stdout.write(self.style.SUCCESS('✓ Created wishlist items and quiz attempts'))
    
    def create_blog_posts(self):
        """Create Islamic blog posts"""
        self.stdout.write(self.style.SUCCESS('\n7. CREATING BLOG POSTS'))
        
        blog_posts = [
            {
                'title': 'The Importance of Seeking Islamic Knowledge',
                'category': 'islamic_knowledge',
                'excerpt': 'Understanding why seeking knowledge is obligatory for every Muslim.',
                'content': 'Detailed article about the importance of Islamic knowledge...',
                'featured': True
            },
            {
                'title': '10 Tips for Effective Quran Memorization',
                'category': 'quran_studies',
                'excerpt': 'Practical tips to help you memorize Quran efficiently.',
                'content': 'Comprehensive guide to Quran memorization techniques...',
                'featured': True
            },
            {
                'title': 'The Life of Prophet Muhammad (PBUH): Lessons for Today',
                'category': 'sunnah',
                'excerpt': 'How Prophet Muhammad\'s life provides guidance for modern Muslims.',
                'content': 'Analysis of Prophet\'s life and contemporary applications...',
                'featured': False
            },
            {
                'title': 'Balancing Studies and Spiritual Growth',
                'category': 'student_life',
                'excerpt': 'Tips for maintaining spiritual growth while pursuing education.',
                'content': 'Guide to balancing worldly and religious education...',
                'featured': False
            },
            {
                'title': 'New Course Announcement: Advanced Tajweed',
                'category': 'announcements',
                'excerpt': 'Announcing our new advanced Tajweed course starting next month.',
                'content': 'Details about the new advanced Tajweed course...',
                'featured': True
            },
        ]
        
        admin_user = User.objects.get(username='admin')
        for post_data in blog_posts:
            post = BlogPost.objects.create(
                title=post_data['title'],
                slug=slugify(post_data['title']),
                category=post_data['category'],
                excerpt=post_data['excerpt'],
                content=post_data['content'] * 5,  # Make content longer
                author=admin_user,
                is_published=True,
                is_featured=post_data['featured'],
                published_at=timezone.now() - timedelta(days=random.randint(1, 90)),
                views=random.randint(100, 1000),
                likes=random.randint(50, 500)
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Blog post: {post.title}'))
    
    def create_faq(self):
        """Create FAQ entries"""
        self.stdout.write(self.style.SUCCESS('\n8. CREATING FAQ ENTRIES'))
        
        faq_data = [
            {
                'question': 'How do I enroll in a course?',
                'answer': 'Click on any course, then click "Enroll Now". Follow the payment process if it\'s a paid course.',
                'category': 'admission'
            },
            {
                'question': 'Are courses self-paced or scheduled?',
                'answer': 'We offer both! Check course details for specific information.',
                'category': 'courses'
            },
            {
                'question': 'What payment methods do you accept?',
                'answer': 'bKash, Nagad, Rocket, bank transfer, and credit cards.',
                'category': 'payment'
            },
            {
                'question': 'Will I get a certificate?',
                'answer': 'Yes, most courses offer certificates upon successful completion.',
                'category': 'general'
            },
            {
                'question': 'Can I access courses on mobile?',
                'answer': 'Yes, our platform is fully responsive and works on all devices.',
                'category': 'technical'
            },
        ]
        
        for idx, data in enumerate(faq_data, 1):
            FAQ.objects.create(
                question=data['question'],
                answer=data['answer'],
                category=data['category'],
                display_order=idx,
                is_active=True
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created 5 FAQ entries'))
    
    def create_resources(self):
        """Create course resources"""
        self.stdout.write(self.style.SUCCESS('\n9. CREATING COURSE RESOURCES'))
        
        resource_types = ['pdf', 'link', 'document', 'presentation']
        
        for course in self.courses[:10]:  # Add resources to first 10 courses
            resource_count = random.randint(2, 5)
            for i in range(resource_count):
                CourseResource.objects.create(
                    course=course,
                    title=f"Resource {i+1} for {course.name.split('-')[0].strip()}",
                    description=f"Additional learning material for {course.name}",
                    resource_type=random.choice(resource_types),
                    is_free=random.choice([True, False]),
                    order=i+1,
                    is_active=True
                )
        
        self.stdout.write(self.style.SUCCESS('✓ Created resources for 10 courses'))
    
    def create_reviews(self):
        """Create course reviews"""
        self.stdout.write(self.style.SUCCESS('\n10. CREATING COURSE REVIEWS'))
        
        review_count = 0
        for course in self.courses:
            # Get students enrolled in this course
            enrollments = Enrollment.objects.filter(course=course, enrollment_status__in=['active', 'completed'])
            
            for enrollment in enrollments[:random.randint(1, 3)]:  # 1-3 reviews per course
                student = enrollment.student
                if not CourseReview.objects.filter(student=student, course=course).exists():
                    CourseReview.objects.create(
                        student=student,
                        course=course,
                        enrollment=enrollment,
                        rating=random.randint(4, 5),
                        title=f"Excellent {course.name.split('-')[0].strip()} Course",
                        content=f"This course transformed my understanding. The instructor was knowledgeable and materials were comprehensive. Highly recommended!",
                        is_verified=True,
                        is_published=True,
                        is_helpful=True
                    )
                    review_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {review_count} course reviews'))
    
    def create_certificates(self):
        """Create certificates for completed courses"""
        self.stdout.write(self.style.SUCCESS('\n11. CREATING CERTIFICATES'))
        
        completed_enrollments = Enrollment.objects.filter(
            enrollment_status='completed',
            certificate_issued=False
        )
        
        for enrollment in completed_enrollments[:10]:  # Create certificates for 10 completions
            certificate = Certificate.objects.create(
                enrollment=enrollment,
                student=enrollment.student,
                course=enrollment.course,
                student_name=enrollment.student.full_name,
                course_name=enrollment.course.name,
                completion_date=enrollment.start_date + timedelta(days=random.randint(30, 180)),
                grade=random.choice(['A+', 'A', 'A-', 'B+']),
                final_score=random.uniform(85.0, 97.5),
                is_verified=True,
                signed_by=enrollment.course.course_instructors.first().instructor.full_name if enrollment.course.course_instructors.exists() else "Taw Haa Zin Nurain"
            )
            
            enrollment.certificate_issued = True
            enrollment.certificate_issue_date = certificate.completion_date
            enrollment.certificate_id = certificate.certificate_id
            enrollment.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {min(10, completed_enrollments.count())} certificates'))
    
    def create_gallery(self):
        """Create gallery images"""
        self.stdout.write(self.style.SUCCESS('\n12. CREATING GALLERY'))
        
        gallery_items = [
            {'title': 'Classroom Session', 'category': 'classroom'},
            {'title': 'Quran Recitation Competition', 'category': 'events'},
            {'title': 'Student Study Group', 'category': 'students'},
            {'title': 'Teacher Lecture', 'category': 'teachers'},
            {'title': 'Campus View', 'category': 'campus'},
        ]
        
        for item in gallery_items:
            Gallery.objects.create(
                title=item['title'],
                description=f"Photo from {item['title'].lower()}",
                category=item['category'],
                is_featured=random.choice([True, False]),
                event_date=timezone.now().date() - timedelta(days=random.randint(1, 365))
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created gallery items'))
    
    def create_donations(self):
        """Create donation records"""
        self.stdout.write(self.style.SUCCESS('\n13. CREATING DONATIONS'))
        
        donor_names = ['Abdullah Khan', 'Fatima Begum', 'Mohammad Ali', 'Aisha Rahman', 'Support Foundation']
        
        for i, name in enumerate(donor_names, 1):
            Donation.objects.create(
                donor_name=name,
                donor_email=f'donor{i}@example.com',
                donor_phone=f'+88017{random.randint(1000000, 9999999)}',
                amount=Decimal(random.randint(1000, 50000)),
                payment_method=random.choice(['bkash', 'nagad', 'bank']),
                transaction_id=f'DON{random.randint(100000, 999999)}',
                purpose=random.choice(['General Donation', 'Student Scholarship', 'Course Development']),
                is_zakat=random.choice([True, False]),
                is_sadaqah=random.choice([True, False]),
                is_verified=True
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Created donation records'))
    
    def print_summary(self):
        """Print summary of created data"""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('TEST DATA CREATION COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        summary = {
            'Users': User.objects.count(),
            'Students': Student.objects.count(),
            'Instructors': Instructor.objects.count(),
            'Categories': Category.objects.count(),
            'Courses': Course.objects.count(),
            'Modules': Module.objects.count(),
            'Lessons': Lesson.objects.count(),
            'Quizzes': Quiz.objects.count(),
            'Quiz Questions': QuizQuestion.objects.count(),
            'Enrollments': Enrollment.objects.count(),
            'Payments': Payment.objects.count(),
            'Wishlist Items': Wishlist.objects.count(),
            'Course Reviews': CourseReview.objects.count(),
            'Certificates': Certificate.objects.count(),
            'Blog Posts': BlogPost.objects.count(),
            'FAQ Entries': FAQ.objects.count(),
            'Coupons': Coupon.objects.count(),
            'Donations': Donation.objects.count(),
            'Gallery Items': Gallery.objects.count(),
        }
        
        for key, value in summary.items():
            self.stdout.write(self.style.SUCCESS(f"{key:20}: {value}"))
        
        # Print login credentials
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('LOGIN CREDENTIALS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS("Admin:     username='admin', password='admin123'"))
        self.stdout.write(self.style.SUCCESS("Instructor1: username='instructor1', password='instructor123'"))
        self.stdout.write(self.style.SUCCESS("Student1:   username='student1', password='student123'"))
        self.stdout.write(self.style.SUCCESS("Student2:   username='student2', password='student123'"))
        
        # Print coupon codes
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('COUPON CODES FOR DISCOUNT'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        for coupon in self.coupons:
            self.stdout.write(self.style.SUCCESS(
                f"{coupon.code}: {coupon.discount_value}{'%' if coupon.discount_type == 'percentage' else '৳'} off"
            ))
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('NEXT STEPS:'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS("1. Run 'python manage.py runserver'"))
        self.stdout.write(self.style.SUCCESS("2. Visit http://127.0.0.1:8000"))
        self.stdout.write(self.style.SUCCESS("3. Login with above credentials"))
        self.stdout.write(self.style.SUCCESS("4. Test all features including wishlist, coupons, and learning"))
        self.stdout.write(self.style.SUCCESS("5. Check admin panel at http://127.0.0.1:8000/admin"))