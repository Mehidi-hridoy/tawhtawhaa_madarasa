# core/management/commands/demo_quan_learning.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
import random
from decimal import Decimal
from datetime import timedelta

# Import all your models
from core.models import (
    Category, Course, CourseInstructor, Instructor, Student, Module, Lesson, 
    Quiz, QuizQuestion, Enrollment, StudentCourseProgress, StudentLessonProgress,
    StudentQuizAttempt, QuizResponse, Payment, Certificate, CourseResource,
    CourseReview, Coupon, Notification, BlogPost, Gallery, Donation, FAQ, ContactMessage
)


class Command(BaseCommand):
    help = 'Create complete demo data for Quran Learning Platform'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating demo data',
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()
        
        self.stdout.write(self.style.SUCCESS('Starting demo data creation...'))
        
        with transaction.atomic():
            # Create superuser
            admin = self.create_admin_user()
            
            # Create users
            users = self.create_users()
            
            # Create categories
            categories = self.create_categories()
            
            # Create courses
            courses = self.create_courses(categories, admin)
            
            # Create instructors
            instructors = self.create_instructors(users[:3])
            
            # Create students
            students = self.create_students(users[3:])
            
            # Assign instructors to courses
            self.assign_instructors(courses, instructors)
            
            # Create course modules
            modules = self.create_modules(courses)
            
            # Create lessons
            self.create_lessons(modules)
            
            # Create quizzes
            quizzes = self.create_quizzes(modules, courses)
            
            # Create MCQ questions
            self.create_mcq_questions(quizzes)
            
            # Create enrollments
            enrollments = self.create_enrollments(students, courses)
            
            # Create course progress
            self.create_course_progress(enrollments)
            
            # Create lesson progress
            self.create_lesson_progress(students, enrollments)
            
            # Create quiz attempts
            self.create_quiz_attempts(students, quizzes, enrollments)
            
            # Create payments
            self.create_payments(enrollments, students)
            
            # Create certificates
            self.create_certificates(enrollments)
            
            # Create course resources (textbook recommendations)
            self.create_textbook_resources(courses)
            
            # Create course reviews
            self.create_course_reviews(students, courses, enrollments)
            
            # Create coupons
            self.create_coupons(courses, admin)
            
            # Create notifications
            self.create_notifications(users, enrollments, courses)
            
            # Create blog posts
            self.create_blog_posts(admin)
            
            # Create gallery items
            self.create_gallery_items(students, courses)
            
            # Create donations
            self.create_donations()
            
            # Create FAQs
            self.create_faqs()
            
            # Create contact messages
            self.create_contact_messages(students, courses, enrollments)
        
        self.stdout.write(self.style.SUCCESS('✅ Demo data created successfully!'))
        self.display_summary()
    
    def create_admin_user(self):
        """Create admin user"""
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@quanlearning.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('admin123')
        admin.save()
        self.stdout.write(self.style.SUCCESS(f'✅ Created admin user: {admin.username}'))
        return admin
    
    def create_users(self):
        """Create demo users"""
        users_data = [
            {'username': 'instructor1', 'email': 'instructor1@quanlearning.com', 
             'first_name': 'Muhammad', 'last_name': 'Ali', 'is_staff': True},
            {'username': 'instructor2', 'email': 'instructor2@quanlearning.com', 
             'first_name': 'Fatima', 'last_name': 'Khan', 'is_staff': True},
            {'username': 'instructor3', 'email': 'instructor3@quanlearning.com', 
             'first_name': 'Abdullah', 'last_name': 'Rahman', 'is_staff': True},
            {'username': 'student1', 'email': 'student1@quanlearning.com', 
             'first_name': 'Ahmed', 'last_name': 'Hossain'},
            {'username': 'student2', 'email': 'student2@quanlearning.com', 
             'first_name': 'Aisha', 'last_name': 'Begum'},
            {'username': 'student3', 'email': 'student3@quanlearning.com', 
             'first_name': 'Ibrahim', 'last_name': 'Chowdhury'},
            {'username': 'student4', 'email': 'student4@quanlearning.com', 
             'first_name': 'Sara', 'last_name': 'Islam'},
            {'username': 'student5', 'email': 'student5@quanlearning.com', 
             'first_name': 'Yusuf', 'last_name': 'Ahmed'},
        ]
        
        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_staff': user_data.get('is_staff', False),
                }
            )
            user.set_password('password123')
            user.save()
            users.append(user)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created user: {user.username}'))
        
        return users
    
    def create_categories(self):
        """Create Quran learning categories"""
        categories_data = [
            {
                'name': 'Quran Recitation',
                'description': 'Learn proper Quran recitation (Tajweed) with correct pronunciation',
                'icon_class': 'fas fa-quran',
                'color': '#4CAF50',
                'meta_title': 'Quran Recitation Courses - Learn Tajweed Online',
            },
            {
                'name': 'Quran Memorization',
                'description': 'Hifz programs for Quran memorization with expert guidance',
                'icon_class': 'fas fa-brain',
                'color': '#2196F3',
                'meta_title': 'Quran Memorization (Hifz) Courses Online',
            },
            {
                'name': 'Quran Translation',
                'description': 'Understand Quran meanings with translation and Tafsir',
                'icon_class': 'fas fa-language',
                'color': '#FF9800',
                'meta_title': 'Quran Translation and Tafsir Courses',
            },
            {
                'name': 'Islamic Studies',
                'description': 'Comprehensive Islamic knowledge including Hadith and Fiqh',
                'icon_class': 'fas fa-mosque',
                'color': '#9C27B0',
                'meta_title': 'Online Islamic Studies Courses',
            },
            {
                'name': 'Arabic Language',
                'description': 'Learn Arabic to understand Quran directly',
                'icon_class': 'fas fa-font',
                'color': '#F44336',
                'meta_title': 'Arabic Language Courses for Quran Understanding',
            },
        ]
        
        categories = []
        for i, cat_data in enumerate(categories_data):
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon_class': cat_data['icon_class'],
                    'color': cat_data['color'],
                    'display_order': i,
                    'meta_title': cat_data['meta_title'],
                    'meta_description': cat_data['description'][:200],
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created category: {category.name}'))
        
        return categories
    
    def create_courses(self, categories, admin):
        """Create Quran learning courses"""
        courses_data = [
            {
                'name': 'Basic Quran Reading with Tajweed',
                'category': categories[0],
                'description': 'Learn to read Quran correctly with proper Tajweed rules. Perfect for beginners.',
                'short_description': 'Master Quran reading with proper pronunciation',
                'learning_outcomes': '• Read Quran with correct pronunciation\n• Understand basic Tajweed rules\n• Recite short Surahs correctly',
                'course_type': 'self_paced',
                'level': 'beginner',
                'price_type': 'free',
                'base_price': 0.00,
                'estimated_duration_hours': 40,
                'access_duration_days': 365,
                'is_featured': True,
                'certificate_available': True,
            },
            {
                'name': 'Quran Memorization (Hifz) - Level 1',
                'category': categories[1],
                'description': 'Start your journey of Quran memorization with structured lessons and revision system.',
                'short_description': 'Begin your Hifz journey with expert guidance',
                'learning_outcomes': '• Memorize last 10 Surahs\n• Learn memorization techniques\n• Understand revision methods',
                'course_type': 'instructor_led',
                'level': 'beginner',
                'price_type': 'paid',
                'base_price': 5000.00,
                'sale_price': 4000.00,
                'estimated_duration_hours': 120,
                'access_duration_days': 730,
                'is_featured': True,
                'certificate_available': True,
            },
            {
                'name': 'Quran Translation and Tafsir - Juz Amma',
                'category': categories[2],
                'description': 'Understand the meaning of last 10 Surahs with detailed explanation and practical lessons.',
                'short_description': 'Deep dive into meanings of last 10 Surahs',
                'learning_outcomes': '• Understand word-by-word translation\n• Learn Tafsir of Surahs\n• Apply lessons in daily life',
                'course_type': 'hybrid',
                'level': 'intermediate',
                'price_type': 'paid',
                'base_price': 3000.00,
                'estimated_duration_hours': 60,
                'access_duration_days': 365,
                'is_featured': False,
                'certificate_available': True,
            },
            {
                'name': 'Advanced Tajweed Rules',
                'category': categories[0],
                'description': 'Master advanced Tajweed rules for perfect Quran recitation.',
                'short_description': 'Perfect your Quran recitation skills',
                'learning_outcomes': '• Master advanced Tajweed\n• Learn rules of Waqf\n• Perfect Makharij and Sifat',
                'course_type': 'instructor_led',
                'level': 'advanced',
                'price_type': 'paid',
                'base_price': 4000.00,
                'estimated_duration_hours': 80,
                'access_duration_days': 365,
                'is_featured': True,
                'certificate_available': True,
            },
            {
                'name': 'Basic Arabic for Quran Understanding',
                'category': categories[4],
                'description': 'Learn Arabic grammar and vocabulary to understand Quran directly.',
                'short_description': 'Learn Arabic to understand Quran',
                'learning_outcomes': '• Understand basic Arabic grammar\n• Learn Quranic vocabulary\n• Read simple Arabic texts',
                'course_type': 'self_paced',
                'level': 'beginner',
                'price_type': 'free',
                'base_price': 0.00,
                'estimated_duration_hours': 50,
                'access_duration_days': 365,
                'is_featured': False,
                'certificate_available': True,
            },
        ]
        
        courses = []
        for i, course_data in enumerate(courses_data):
            course, created = Course.objects.get_or_create(
                name=course_data['name'],
                defaults={
                    'category': course_data['category'],
                    'description': course_data['description'],
                    'short_description': course_data['short_description'],
                    'learning_outcomes': course_data['learning_outcomes'],
                    'course_type': course_data['course_type'],
                    'level': course_data['level'],
                    'price_type': course_data['price_type'],
                    'base_price': course_data['base_price'],
                    'sale_price': course_data.get('sale_price'),
                    'estimated_duration_hours': course_data['estimated_duration_hours'],
                    'access_duration_days': course_data['access_duration_days'],
                    'is_featured': course_data['is_featured'],
                    'certificate_available': course_data['certificate_available'],
                    'created_by': admin,
                    'is_approved': True,
                    'is_active': True,
                    'published_at': timezone.now(),
                    'meta_title': f'{course_data["name"]} - Online Quran Learning',
                    'meta_description': course_data['short_description'],
                }
            )
            courses.append(course)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created course: {course.name}'))
        
        return courses
    
    def create_instructors(self, users):
        """Create instructor profiles"""
        instructors_data = [
            {
                'user': users[0],
                'full_name': 'Muhammad Ali Al-Azhari',
                'bio': 'Graduate from Al-Azhar University with 15 years of teaching experience. Specialized in Tajweed and Quran Memorization.',
                'specialization': 'Tajweed, Hifz, Quranic Sciences',
                'role': 'lead',
                'experience_years': 15,
                'qualifications': 'Al-Azhar University Graduate, Ijazah in Hafs & Shu\'bah, Certified Tajweed Teacher',
                'phone': '+8801711111111',
                'email': 'm.ali@quanlearning.com',
                'is_active': True,
            },
            {
                'user': users[1],
                'full_name': 'Fatima Khan',
                'bio': 'Female Quran teacher specializing in teaching women and children. Graduated from Islamic University of Medina.',
                'specialization': 'Quran Recitation, Islamic Studies, Women Education',
                'role': 'senior',
                'experience_years': 10,
                'qualifications': 'Islamic University of Medina, Ijazah in Qalun, Certified Female Quran Teacher',
                'phone': '+8801722222222',
                'email': 'fatima.khan@quanlearning.com',
                'is_active': True,
            },
            {
                'user': users[2],
                'full_name': 'Abdullah Rahman',
                'bio': 'Expert in Quran Translation and Tafsir. PhD in Islamic Studies from International Islamic University.',
                'specialization': 'Quran Translation, Tafsir, Arabic Language',
                'role': 'senior',
                'experience_years': 12,
                'qualifications': 'PhD Islamic Studies, MA Arabic Language, Certified Translator',
                'phone': '+8801733333333',
                'email': 'abdullah@quanlearning.com',
                'is_active': True,
            },
        ]
        
        instructors = []
        for instr_data in instructors_data:
            instructor, created = Instructor.objects.get_or_create(
                user=instr_data['user'],
                defaults=instr_data
            )
            instructors.append(instructor)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created instructor: {instructor.full_name}'))
        
        return instructors
    
    def create_students(self, users):
        """Create student profiles"""
        students = []
        for i, user in enumerate(users):
            student, created = Student.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': f'{user.first_name} {user.last_name}',
                    'phone': f'+88017{5000000 + i}',
                    'address': f'House {i+1}, Road {i+1}, Dhaka',
                    'city': 'Dhaka',
                    'country': 'Bangladesh',
                    'occupation': 'student' if i < 2 else 'professional',
                    'education_level': 'Bachelor' if i < 2 else 'Master',
                    'about_me': f'Passionate about learning Quran and Islamic knowledge. Student at Quran Learning Platform.',
                    'preferred_language': 'en',
                    'is_active': True,
                    'email_verified': True,
                }
            )
            students.append(student)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created student: {student.full_name}'))
        
        return students
    
    def assign_instructors(self, courses, instructors):
        """Assign instructors to courses"""
        assignments = [
            (courses[0], [instructors[0], instructors[1]]),  # Basic Quran Reading
            (courses[1], [instructors[0]]),  # Hifz Level 1
            (courses[2], [instructors[2]]),  # Quran Translation
            (courses[3], [instructors[0], instructors[2]]),  # Advanced Tajweed
            (courses[4], [instructors[1], instructors[2]]),  # Arabic for Quran
        ]
        
        for course, course_instructors in assignments:
            for i, instructor in enumerate(course_instructors):
                ci, created = CourseInstructor.objects.get_or_create(
                    course=course,
                    instructor=instructor,
                    defaults={'display_order': i}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Assigned {instructor.full_name} to {course.name}'))
    
    def create_modules(self, courses):
        """Create course modules"""
        all_modules = []
        module_data = {
            courses[0]: [  # Basic Quran Reading
                {'title': 'Introduction to Quran Reading', 'order': 1, 'duration_minutes': 120},
                {'title': 'Arabic Alphabet Mastery', 'order': 2, 'duration_minutes': 300},
                {'title': 'Basic Tajweed Rules', 'order': 3, 'duration_minutes': 240},
                {'title': 'Reading Practice Sessions', 'order': 4, 'duration_minutes': 360},
                {'title': 'Final Assessment', 'order': 5, 'duration_minutes': 60},
            ],
            courses[1]: [  # Hifz Level 1
                {'title': 'Introduction to Hifz', 'order': 1, 'duration_minutes': 180},
                {'title': 'Surah Al-Fatihah & Short Surahs', 'order': 2, 'duration_minutes': 600},
                {'title': 'Memorization Techniques', 'order': 3, 'duration_minutes': 240},
                {'title': 'Revision System', 'order': 4, 'duration_minutes': 300},
                {'title': 'Final Test', 'order': 5, 'duration_minutes': 120},
            ],
            courses[2]: [  # Quran Translation
                {'title': 'Introduction to Quran Translation', 'order': 1, 'duration_minutes': 120},
                {'title': 'Surah An-Nas to Surah Al-Adiyat', 'order': 2, 'duration_minutes': 480},
                {'title': 'Word-by-Word Analysis', 'order': 3, 'duration_minutes': 360},
                {'title': 'Tafsir Lessons', 'order': 4, 'duration_minutes': 420},
                {'title': 'Practical Applications', 'order': 5, 'duration_minutes': 180},
            ],
        }
        
        for course, modules_list in module_data.items():
            for mod_data in modules_list:
                module, created = Module.objects.get_or_create(
                    course=course,
                    title=mod_data['title'],
                    defaults={
                        'description': f'Module {mod_data["order"]}: {mod_data["title"]} for {course.name}',
                        'order': mod_data['order'],
                        'duration_minutes': mod_data['duration_minutes'],
                        'is_published': True,
                    }
                )
                all_modules.append(module)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created module: {module.title}'))
        
        return all_modules
    
    def create_lessons(self, modules):
        """Create lessons for modules"""
        lesson_counter = 0
        
        for module in modules:
            lesson_count = random.randint(3, 6)
            for i in range(1, lesson_count + 1):
                lesson_types = ['video', 'article', 'quiz']
                lesson_type = random.choice(lesson_types)
                
                lesson_title = self.generate_lesson_title(module, i)
                
                lesson, created = Lesson.objects.get_or_create(
                    module=module,
                    title=lesson_title,
                    defaults={
                        'lesson_type': lesson_type,
                        'description': f'This is lesson {i} of module "{module.title}". Learn important concepts and practice.',
                        'content': self.generate_lesson_content(module, i),
                        'order': i,
                        'duration_minutes': random.randint(15, 45),
                        'is_published': True,
                        'is_free': True if i <= 2 else random.choice([True, False]),
                        'require_completion': True,
                        'points_value': random.randint(10, 30),
                        'enable_comments': True,
                        'video_url': 'https://www.youtube.com/watch?v=example' if lesson_type == 'video' else '',
                        'video_source': 'youtube' if lesson_type == 'video' else '',
                    }
                )
                lesson_counter += 1
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created lesson: {lesson.title}'))
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {lesson_counter} lessons total'))
    
    def generate_lesson_title(self, module, lesson_num):
        """Generate appropriate lesson title based on module"""
        titles_map = {
            'Arabic Alphabet': ['Arabic Letters Introduction', 'Letter Forms', 'Pronunciation Practice', 'Writing Practice'],
            'Tajweed': ['Makharij Introduction', 'Sifatul Huruf', 'Rules of Noon and Meem', 'Waqf Rules'],
            'Hifz': ['Memorization Method', 'Revision Technique', 'Recitation Practice', 'Test Preparation'],
            'Translation': ['Word Analysis', 'Grammar Rules', 'Context Understanding', 'Practical Application'],
        }
        
        for key, titles in titles_map.items():
            if key.lower() in module.title.lower():
                return titles[min(lesson_num - 1, len(titles) - 1)]
        
        return f'Learning Session {lesson_num}'
    
    def generate_lesson_content(self, module, lesson_num):
        """Generate lesson content based on module"""
        contents = {
            'Arabic Alphabet': f"""
            <h3>Arabic Alphabet Lesson {lesson_num}</h3>
            <p>In this lesson, we will learn about Arabic letters and their proper pronunciation.</p>
            <ul>
                <li>Learn letter shapes</li>
                <li>Practice pronunciation</li>
                <li>Writing exercises</li>
            </ul>
            """,
            'Tajweed': f"""
            <h3>Tajweed Rules Lesson {lesson_num}</h3>
            <p>Master the art of Quran recitation with proper Tajweed rules.</p>
            <p>This lesson covers essential Tajweed principles that every reciter must know.</p>
            """,
            'Hifz': f"""
            <h3>Memorization Session {lesson_num}</h3>
            <p>Effective techniques for Quran memorization and retention.</p>
            <p>Practice with repetition and understanding for better memorization.</p>
            """,
            'Translation': f"""
            <h3>Quran Translation Lesson {lesson_num}</h3>
            <p>Understanding Quranic Arabic and translation methods.</p>
            <p>Learn to translate Quran verses with proper context and meaning.</p>
            """,
        }
        
        for key in contents:
            if key.lower() in module.title.lower():
                return contents[key]
        
        return f"<h3>Lesson {lesson_num}</h3><p>This is lesson {lesson_num} content for {module.title}.</p>"
    
    def create_quizzes(self, modules, courses):
        """Create quizzes for lessons, modules, and courses"""
        quizzes = []
        
        # Get some lessons for lesson quizzes
        lessons = Lesson.objects.filter(module__in=modules)[:5]
        
        # Create lesson quizzes
        for lesson in lessons:
            quiz, created = Quiz.objects.get_or_create(
                lesson=lesson,
                defaults={
                    'quiz_type': 'practice',
                    'description': f'Practice quiz for {lesson.title}',
                    'duration_minutes': 15,
                    'passing_score': 70,
                    'max_attempts': 3,
                    'show_correct_answers': True,
                    'randomize_questions': True,
                    'total_points': 100,
                    'is_published': True,
                    'is_active': True,
                }
            )
            quizzes.append(quiz)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created quiz for lesson: {lesson.title}'))
        
        # Create module quiz
        if modules:
            module_quiz, created = Quiz.objects.get_or_create(
                module=modules[0],
                defaults={
                    'quiz_type': 'module',
                    'description': 'End of module assessment',
                    'duration_minutes': 30,
                    'passing_score': 80,
                    'max_attempts': 2,
                    'require_passing': True,
                    'total_points': 100,
                    'is_published': True,
                }
            )
            quizzes.append(module_quiz)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created module quiz: {modules[0].title}'))
        
        # Create final exam
        if courses:
            final_exam, created = Quiz.objects.get_or_create(
                course=courses[0],
                quiz_type='final',
                defaults={
                    'description': 'Final examination for course completion',
                    'duration_minutes': 60,
                    'passing_score': 75,
                    'max_attempts': 1,
                    'require_passing': True,
                    'total_points': 100,
                    'weight_percentage': 40,
                    'is_published': True,
                }
            )
            quizzes.append(final_exam)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created final exam for: {courses[0].name}'))
        
        return quizzes
    
    def create_mcq_questions(self, quizzes):
        """Create 5 MCQ questions for quizzes"""
        questions_data = [
            {
                'question_text': 'What is the meaning of "Iqra" in Quran?',
                'options': ['Read', 'Pray', 'Listen', 'Write'],
                'correct_answers': [0],  # First option is correct
                'explanation': 'The first word revealed to Prophet Muhammad (PBUH) was "Iqra" which means "Read".',
                'points': 20,
            },
            {
                'question_text': 'Which Surah is called the "Heart of the Quran"?',
                'options': ['Surah Al-Fatihah', 'Surah Yasin', 'Surah Al-Baqarah', 'Surah Al-Ikhlas'],
                'correct_answers': [1],  # Surah Yasin
                'explanation': 'Surah Yasin is often referred to as the "Heart of the Quran" due to its importance.',
                'points': 20,
            },
            {
                'question_text': 'What is the total number of Surahs in the Quran?',
                'options': ['99', '114', '120', '666'],
                'correct_answers': [1],  # 114
                'explanation': 'The Quran contains 114 Surahs (chapters) in total.',
                'points': 10,
            },
            {
                'question_text': 'Which of the following are pillars of Islam? (Select all that apply)',
                'question_type': 'mcq_multiple',
                'options': ['Shahadah', 'Salah', 'Zakat', 'Sawm', 'Hajj'],
                'correct_answers': [0, 1, 2, 3, 4],  # All are correct
                'explanation': 'The five pillars of Islam are: Shahadah, Salah, Zakat, Sawm, and Hajj.',
                'points': 25,
            },
            {
                'question_text': 'Who was the first recipient of the Quranic revelation?',
                'options': ['Prophet Muhammad (PBUH)', 'Angel Jibreel (AS)', 'Khadijah (RA)', 'Abu Bakr (RA)'],
                'correct_answers': [0],  # Prophet Muhammad
                'explanation': 'The Quran was revealed to Prophet Muhammad (PBUH) through Angel Jibreel (AS).',
                'points': 15,
            },
        ]
        
        for quiz in quizzes[:2]:  # Add questions to first 2 quizzes
            for i, q_data in enumerate(questions_data):
                question, created = QuizQuestion.objects.get_or_create(
                    quiz=quiz,
                    question_text=q_data['question_text'],
                    defaults={
                        'question_type': q_data.get('question_type', 'mcq_single'),
                        'explanation': q_data['explanation'],
                        'points': q_data['points'],
                        'order': i + 1,
                        'options': q_data['options'],
                        'correct_answers': q_data['correct_answers'],
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created MCQ question: {question.question_text[:50]}...'))
    
    def create_enrollments(self, students, courses):
        """Create course enrollments"""
        enrollments = []
        
        # Enroll students in courses
        for student in students[:3]:  # First 3 students
            for course in courses[:3]:  # First 3 courses
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'start_date': timezone.now().date(),
                        'end_date': (timezone.now() + timedelta(days=course.access_duration_days)).date(),
                        'enrollment_status': 'active',
                        'payment_status': 'paid' if course.price_type == 'paid' else 'pending',
                        'progress_percentage': random.randint(20, 80),
                        'amount_paid': course.get_current_price() if course.price_type == 'paid' else 0,
                    }
                )
                enrollments.append(enrollment)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Enrolled {student.full_name} in {course.name}'))
        
        return enrollments
    
    def create_course_progress(self, enrollments):
        """Create course progress records"""
        for enrollment in enrollments:
            progress, created = StudentCourseProgress.objects.get_or_create(
                student=enrollment.student,
                course=enrollment.course,
                enrollment=enrollment,
                defaults={
                    'overall_progress': enrollment.progress_percentage,
                    'completed_lessons': random.randint(1, 10),
                    'total_lessons': 15,
                    'total_points': random.randint(100, 500),
                    'total_time_spent': random.randint(300, 1800),  # 5-30 hours in minutes
                    'is_completed': enrollment.progress_percentage >= 100,
                    'completed_at': timezone.now() if enrollment.progress_percentage >= 100 else None,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created course progress for {enrollment.student.full_name}'))
    
    def create_lesson_progress(self, students, enrollments):
        """Create lesson progress records"""
        for enrollment in enrollments[:2]:  # For first 2 enrollments
            # Get lessons for this course
            course_lessons = Lesson.objects.filter(module__course=enrollment.course)[:5]
            
            for lesson in course_lessons:
                progress, created = StudentLessonProgress.objects.get_or_create(
                    student=enrollment.student,
                    lesson=lesson,
                    enrollment=enrollment,
                    defaults={
                        'status': random.choice(['completed', 'in_progress', 'not_started']),
                        'started_at': timezone.now() if random.choice([True, False]) else None,
                        'completed_at': timezone.now() if random.choice([True, False]) else None,
                        'video_progress_seconds': random.randint(0, 600),
                        'points_earned': lesson.points_value if random.choice([True, False]) else 0,
                        'attempts_count': random.randint(0, 3),
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created lesson progress for {enrollment.student.full_name}'))
    
    def create_quiz_attempts(self, students, quizzes, enrollments):
        """Create quiz attempts"""
        for student in students[:2]:
            for quiz in quizzes[:2]:
                attempt, created = StudentQuizAttempt.objects.get_or_create(
                    student=student,
                    quiz=quiz,
                    attempt_number=1,
                    defaults={
                        'enrollment': enrollments[0] if enrollments else None,
                        'score': random.randint(60, 95),
                        'total_questions': quiz.questions.count(),
                        'correct_answers': random.randint(3, quiz.questions.count() if quiz.questions.count() > 0 else 5),
                        'is_completed': True,
                        'is_passed': True,
                        'submitted_at': timezone.now(),
                        'time_taken_seconds': random.randint(300, 1800),
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created quiz attempt for {student.full_name}'))
    
    def create_payments(self, enrollments, students):
        """Create payment records for paid courses"""
        for enrollment in enrollments:
            if enrollment.course.price_type == 'paid' and enrollment.payment_status == 'paid':
                payment, created = Payment.objects.get_or_create(
                    enrollment=enrollment,
                    student=enrollment.student,
                    transaction_id=f'TXN{enrollment.id.hex[:8].upper()}',
                    defaults={
                        'amount': enrollment.amount_paid,
                        'payment_method': random.choice(['bkash', 'nagad', 'bank']),
                        'status': 'completed',
                        'is_verified': True,
                        'verified_at': timezone.now(),
                        'verified_by': User.objects.get(username='admin'),
                        'gateway_response': {'status': 'success', 'message': 'Payment completed'},
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created payment for {enrollment.student.full_name}'))
    
    def create_certificates(self, enrollments):
        """Create certificates for completed courses"""
        for enrollment in enrollments[:2]:  # First 2 enrollments get certificates
            if enrollment.progress_percentage >= 100:
                cert, created = Certificate.objects.get_or_create(
                    enrollment=enrollment,
                    defaults={
                        'student': enrollment.student,
                        'course': enrollment.course,
                        'student_name': enrollment.student.full_name,
                        'course_name': enrollment.course.name,
                        'completion_date': enrollment.completed_at.date() if enrollment.completed_at else timezone.now().date(),
                        'grade': random.choice(['A+', 'A', 'A-', 'B+']),
                        'final_score': random.randint(85, 98),
                        'is_verified': True,
                        'template': 'default',
                        'signed_by': 'Director, Quran Learning Platform',
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created certificate for {enrollment.student.full_name}'))
    
    def create_textbook_resources(self, courses):
        """Create textbook recommendations as course resources"""
        textbooks = [
            {
                'title': 'Tajweed Rules of the Quran (3 Part Set)',
                'description': 'Complete guide to Tajweed rules with examples and exercises',
                'resource_type': 'pdf',
                'url': 'https://example.com/tajweed-textbook.pdf',
                'is_free': False,
            },
            {
                'title': 'The Meaning of the Holy Quran - Abdullah Yusuf Ali',
                'description': 'Complete translation and commentary of the Quran',
                'resource_type': 'link',
                'url': 'https://quran.com',
                'is_free': True,
            },
            {
                'title': 'Arabic Course for English-Speaking Students',
                'description': '3 Volume set for learning Arabic to understand Quran',
                'resource_type': 'pdf',
                'url': 'https://example.com/arabic-course.pdf',
                'is_free': False,
            },
            {
                'title': 'Stories of the Prophets - Ibn Kathir',
                'description': 'Comprehensive stories of all prophets mentioned in Quran',
                'resource_type': 'pdf',
                'url': 'https://example.com/prophets-stories.pdf',
                'is_free': True,
            },
            {
                'title': '40 Hadith Nawawi - Arabic with Translation',
                'description': 'Collection of 40 important Hadith with explanations',
                'resource_type': 'document',
                'url': 'https://example.com/40-hadith.pdf',
                'is_free': True,
            },
        ]
        
        for i, textbook in enumerate(textbooks):
            for course in courses[:3]:  # Add to first 3 courses
                resource, created = CourseResource.objects.get_or_create(
                    course=course,
                    title=textbook['title'],
                    defaults={
                        'description': textbook['description'],
                        'resource_type': textbook['resource_type'],
                        'url': textbook['url'],
                        'is_free': textbook['is_free'],
                        'order': i + 1,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Added textbook: {textbook["title"]}'))
    
    def create_course_reviews(self, students, courses, enrollments):
        """Create course reviews"""
        reviews = [
            {
                'rating': 5,
                'title': 'Excellent Course for Beginners',
                'content': 'This course helped me start reading Quran properly. The instructors are very knowledgeable.',
            },
            {
                'rating': 4,
                'title': 'Very Comprehensive',
                'content': 'Good course structure and materials. Could use more practice exercises.',
            },
            {
                'rating': 5,
                'title': 'Life Changing Experience',
                'content': 'Alhamdulillah, I can now read Quran with Tajweed. Thank you to the teachers.',
            },
        ]
        
        for i, student in enumerate(students[:3]):
            for course in courses[:2]:
                review, created = CourseReview.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'enrollment': enrollments[0] if enrollments else None,
                        'rating': reviews[i]['rating'],
                        'title': reviews[i]['title'],
                        'content': reviews[i]['content'],
                        'is_verified': True,
                        'is_published': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✅ Created review by {student.full_name}'))
    
    def create_coupons(self, courses, admin):
        """Create discount coupons"""
        coupons_data = [
            {
                'code': 'QURAN2024',
                'discount_type': 'percentage',
                'discount_value': 20,
                'usage_limit': 100,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
                'minimum_cart_amount': 1000,
            },
            {
                'code': 'RAMADAN24',
                'discount_type': 'fixed',
                'discount_value': 500,
                'usage_limit': 50,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=60),
            },
        ]
        
        for coupon_data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults={
                    'discount_type': coupon_data['discount_type'],
                    'discount_value': coupon_data['discount_value'],
                    'usage_limit': coupon_data['usage_limit'],
                    'valid_from': coupon_data['valid_from'],
                    'valid_until': coupon_data['valid_until'],
                    'minimum_cart_amount': coupon_data.get('minimum_cart_amount', 0),
                    'is_active': True,
                    'created_by': admin,
                }
            )
            if created:
                # Add applicable courses
                coupon.applicable_courses.set(courses[:3])
                self.stdout.write(self.style.SUCCESS(f'✅ Created coupon: {coupon.code}'))
    
    def create_notifications(self, users, enrollments, courses):
        """Create notifications"""
        notifications = [
            {
                'recipient': users[3],  # student1
                'notification_type': 'enrollment',
                'title': 'Welcome to Quran Learning Platform!',
                'message': 'You have successfully enrolled in Basic Quran Reading course.',
                'enrollment': enrollments[0] if enrollments else None,
                'course': courses[0] if courses else None,
            },
            {
                'recipient': users[0],  # instructor1
                'notification_type': 'enrollment',
                'title': 'New Student Enrollment',
                'message': 'A new student has enrolled in your course.',
                'course': courses[0] if courses else None,
            },
            {
                'recipient': users[3],
                'notification_type': 'completion',
                'title': 'Course Completed!',
                'message': 'Congratulations! You have completed Basic Quran Reading course.',
                'course': courses[0] if courses else None,
            },
        ]
        
        for notif_data in notifications:
            notification, created = Notification.objects.get_or_create(
                recipient=notif_data['recipient'],
                title=notif_data['title'],
                defaults={
                    'notification_type': notif_data['notification_type'],
                    'message': notif_data['message'],
                    'is_read': False,
                    'is_sent': True,
                    'enrollment': notif_data.get('enrollment'),
                    'course': notif_data.get('course'),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created notification: {notification.title}'))
    
    def create_blog_posts(self, admin):
        """Create blog posts"""
        posts = [
            {
                'title': 'The Importance of Learning Quran in Modern Times',
                'content': 'In this article, we discuss why learning Quran is essential...',
                'excerpt': 'Understanding the relevance of Quranic education today',
                'category': 'islamic_knowledge',
                'is_published': True,
                'is_featured': True,
            },
            {
                'title': '5 Tips for Effective Quran Memorization',
                'content': 'Memorizing Quran requires dedication and proper techniques...',
                'excerpt': 'Learn proven methods for Quran memorization',
                'category': 'quran_studies',
                'is_published': True,
            },
        ]
        
        for post_data in posts:
            post, created = BlogPost.objects.get_or_create(
                title=post_data['title'],
                defaults={
                    'content': post_data['content'],
                    'excerpt': post_data['excerpt'],
                    'category': post_data['category'],
                    'author': admin,
                    'is_published': post_data['is_published'],
                    'is_featured': post_data.get('is_featured', False),
                    'published_at': timezone.now(),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created blog post: {post.title}'))
    
    def create_gallery_items(self, students, courses):
        """Create gallery items"""
        gallery_items = [
            {
                'title': 'Online Quran Class Session',
                'description': 'Students participating in virtual Quran learning session',
                'category': 'classroom',
                'course': courses[0] if courses else None,
            },
            {
                'title': 'Eid Celebration at Madrassa',
                'description': 'Students celebrating Eid after completing Quran courses',
                'category': 'events',
                'event_date': timezone.now().date(),
            },
        ]
        
        for item_data in gallery_items:
            item, created = Gallery.objects.get_or_create(
                title=item_data['title'],
                defaults=item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created gallery item: {item.title}'))
    
    def create_donations(self):
        """Create donation records"""
        donations = [
            {
                'donor_name': 'Anonymous',
                'donor_email': 'anonymous@example.com',
                'donor_phone': '+8801700000000',
                'amount': 5000.00,
                'payment_method': 'bkash',
                'transaction_id': f'DON{int(timezone.now().timestamp())}',
                'purpose': 'Support Quran Education',
                'is_zakat': True,
                'is_anonymous': True,
                'is_verified': True,
            },
        ]
        
        for donation_data in donations:
            donation, created = Donation.objects.get_or_create(
                transaction_id=donation_data['transaction_id'],
                defaults=donation_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created donation: ৳{donation.amount}'))
    
    def create_faqs(self):
        """Create frequently asked questions"""
        faqs = [
            {
                'question': 'How do I enroll in a course?',
                'answer': 'Click on the course you want to join, then click "Enroll Now" button. Follow the payment process if required.',
                'category': 'admission',
                'display_order': 1,
            },
            {
                'question': 'What are the payment methods available?',
                'answer': 'We accept bKash, Nagad, Rocket, and Bank Transfer.',
                'category': 'payment',
                'display_order': 2,
            },
            {
                'question': 'Do you provide certificates?',
                'answer': 'Yes, we provide digital certificates upon course completion.',
                'category': 'courses',
                'display_order': 3,
            },
        ]
        
        for faq_data in faqs:
            faq, created = FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created FAQ: {faq.question[:50]}...'))
    
    def create_contact_messages(self, students, courses, enrollments):
        """Create contact messages"""
        messages = [
            {
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'Course Enrollment Query',
                'message': 'How can I enroll in the Advanced Tajweed course?',
                'subject_type': 'admission',
                'student': students[0] if students else None,
                'course': courses[0] if courses else None,
            },
        ]
        
        for msg_data in messages:
            message, created = ContactMessage.objects.get_or_create(
                email=msg_data['email'],
                subject=msg_data['subject'],
                defaults=msg_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created contact message from {message.name}'))
    
    def clear_existing_data(self):
        """Clear existing demo data"""
        models_to_clear = [
            ContactMessage, FAQ, Donation, Gallery, BlogPost,
            Notification, Coupon, CourseReview, CourseResource,
            Certificate, Payment, QuizResponse, StudentQuizAttempt,
            StudentLessonProgress, StudentCourseProgress, Enrollment,
            QuizQuestion, Quiz, Lesson, Module, CourseInstructor,
            Instructor, Student, Course, Category
        ]
        
        for model in models_to_clear:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(self.style.WARNING(f'🗑️  Cleared {count} {model.__name__} records'))
        
        # Keep admin user, delete others
        User.objects.exclude(username='admin').delete()
        self.stdout.write(self.style.WARNING('🗑️  Cleared non-admin users'))
    
    def display_summary(self):
        """Display summary of created data"""
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.HTTP_INFO('DEMO DATA SUMMARY'))
        self.stdout.write(self.style.HTTP_INFO('='*60))
        
        summary = {
            'Users': User.objects.count(),
            'Categories': Category.objects.count(),
            'Courses': Course.objects.count(),
            'Instructors': Instructor.objects.count(),
            'Students': Student.objects.count(),
            'Modules': Module.objects.count(),
            'Lessons': Lesson.objects.count(),
            'Quizzes': Quiz.objects.count(),
            'Quiz Questions': QuizQuestion.objects.count(),
            'Enrollments': Enrollment.objects.count(),
            'Course Progress': StudentCourseProgress.objects.count(),
            'Lesson Progress': StudentLessonProgress.objects.count(),
            'Quiz Attempts': StudentQuizAttempt.objects.count(),
            'Payments': Payment.objects.count(),
            'Certificates': Certificate.objects.count(),
            'Textbook Resources': CourseResource.objects.count(),
            'Course Reviews': CourseReview.objects.count(),
            'Coupons': Coupon.objects.count(),
            'Blog Posts': BlogPost.objects.count(),
            'Contact Messages': ContactMessage.objects.count(),
        }
        
        for item, count in summary.items():
            self.stdout.write(self.style.SUCCESS(f'  {item}: {count}'))
        
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write(self.style.SUCCESS('\n📚 TEXTBOOK RECOMMENDATIONS:'))
        textbooks = CourseResource.objects.filter(resource_type__in=['pdf', 'document'])[:5]
        for i, book in enumerate(textbooks, 1):
            self.stdout.write(f'  {i}. {book.title}')
            self.stdout.write(f'     📖 {book.description[:60]}...')
        
        self.stdout.write(self.style.SUCCESS('\n❓ SAMPLE MCQ QUESTIONS:'))
        questions = QuizQuestion.objects.filter(question_type__startswith='mcq')[:5]
        for i, q in enumerate(questions, 1):
            self.stdout.write(f'  {i}. {q.question_text}')
            self.stdout.write(f'     Options: {", ".join(q.options)}')
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ Demo setup complete!'))
        self.stdout.write(self.style.HTTP_INFO('='*60))
        self.stdout.write('\n🔑 Admin Login:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('\n👨‍🎓 Student Login:')
        self.stdout.write('  Username: student1')
        self.stdout.write('  Password: password123')
        self.stdout.write('\n👨‍🏫 Instructor Login:')
        self.stdout.write('  Username: instructor1')
        self.stdout.write('  Password: password123')