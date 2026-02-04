from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid 
from django.db.models import Q, F
from django.utils.text import slugify
import os
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings

# ==================== UTILITY FUNCTIONS ====================
def course_thumbnail_path(instance, filename):
    return f'courses/{instance.id}/thumbnail/{filename}'

def course_featured_image_path(instance, filename):
    return f'courses/{instance.id}/featured/{filename}'

def lesson_video_path(instance, filename):
    # Fixed the path - removed incorrect self_learning_course reference
    if instance.module and instance.module.course:
        return f'courses/{instance.module.course.id}/lessons/{instance.id}/{filename}'
    return f'courses/temp/lessons/{instance.id}/{filename}'

def resource_file_path(instance, filename):
    if instance.course:
        return f'courses/{instance.course.id}/resources/{filename}'
    return f'courses/temp/resources/{filename}'

# ==================== CATEGORY MODEL ====================
class Category(models.Model):
    """Dynamic category model that admin can manage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    icon_class = models.CharField(max_length=50, default='fas fa-book')
    color = models.CharField(max_length=7, default='#4CAF50')  # Hex color
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # SEO Fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_active_courses_count(self):
        return self.courses.filter(is_active=True).count()

# ==================== MAIN COURSE MODEL ====================
class Course(models.Model):
    COURSE_TYPES = [
        ('self_paced', 'Self-Paced'),
        ('instructor_led', 'Instructor-Led'),
        ('hybrid', 'Hybrid'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels'),
    ]
    
    PRICE_TYPES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
        ('subscription', 'Subscription'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    
    # Category (replacing old static categories)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    
    # Course Details
    course_type = models.CharField(max_length=20, choices=COURSE_TYPES, default='self_paced')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    learning_outcomes = models.TextField(blank=True)
    
    # Ratings and Reviews (Added missing fields)
    average_rating = models.FloatField(default=0.0)
    review_count = models.IntegerField(default=0)
    
    # Pricing
    price_type = models.CharField(max_length=20, choices=PRICE_TYPES, default='free')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='BDT')
    
    # Duration
    estimated_duration_hours = models.IntegerField(default=0, help_text="Estimated total duration in hours")
    access_duration_days = models.IntegerField(default=365)  # Days after enrollment
    
    # Multimedia
    thumbnail = models.ImageField(upload_to=course_thumbnail_path, null=True, blank=True)
    featured_image = models.ImageField(upload_to=course_featured_image_path, null=True, blank=True)
    promo_video_url = models.URLField(blank=True)
    
    # Status & Settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    certificate_available = models.BooleanField(default=True)
    requires_completion_certificate = models.BooleanField(default=False)
    
    # Statistics
    total_enrollments = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_price_type_display()})"
    
    def get_current_price(self):
        """Get current price (sale price if available)"""
        if self.sale_price and self.sale_price < self.base_price:
            return self.sale_price
        return self.base_price
    
    def is_free(self):
        return self.price_type == 'free' or self.get_current_price() == 0
    
    def get_discount_percentage(self):
        if self.sale_price and self.base_price > 0:
            discount = ((self.base_price - self.sale_price) / self.base_price) * 100
            return int(discount)
        return 0
    
    def update_statistics(self):
        """Update course statistics"""
        from django.db.models import Count, Q
        self.total_enrollments = self.enrollments.filter(enrollment_status='active').count()
        self.total_completions = self.enrollments.filter(enrollment_status='completed').count()
        self.save()

# ==================== COURSE INSTRUCTORS ====================
class CourseInstructor(models.Model):
    """M2M relationship between Course and Instructor with extra data"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_instructors')
    instructor = models.ForeignKey('Instructor', on_delete=models.CASCADE, related_name='instructor_courses')
    display_order = models.IntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order']
        unique_together = ['course', 'instructor']
    
    def __str__(self):
        return f"{self.instructor.full_name} - {self.course.name}"

# ==================== INSTRUCTOR MODEL ====================
class Instructor(models.Model):
    ROLES = [
        ('lead', 'Lead Instructor'),
        ('senior', 'Senior Instructor'),
        ('assistant', 'Assistant Instructor'),
        ('guest', 'Guest Lecturer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    bio = models.TextField()
    specialization = models.TextField()
    
    # Professional Details
    role = models.CharField(max_length=20, choices=ROLES, default='assistant')
    experience_years = models.IntegerField(default=0)
    qualifications = models.TextField()
    
    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Images
    profile_picture = models.ImageField(upload_to='instructors/profiles/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='instructors/covers/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Statistics
    total_courses = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"
    
    def get_active_courses(self):
        return self.course_instructors.filter(course__is_active=True)
    
    def update_statistics(self):
        """Update instructor statistics"""
        self.total_courses = self.instructor_courses.filter(course__is_active=True).count()
        
        # Count unique students across all courses
        from django.db.models import Count
        student_count = Enrollment.objects.filter(
            course__in=self.instructor_courses.values_list('course', flat=True),
            enrollment_status='active'
        ).values('student').distinct().count()
        self.total_students = student_count
        self.save()

# ==================== STUDENT MODEL ====================
class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    OCCUPATION_CHOICES = [
        ('student', 'Student'),
        ('professional', 'Working Professional'),
        ('business', 'Business Owner'),
        ('housewife', 'Homemaker'),
        ('unemployed', 'Unemployed'),
        ('retired', 'Retired'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    # Background
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES, blank=True)
    education_level = models.CharField(max_length=100, blank=True)
    about_me = models.TextField(blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=50, blank=True, default='en')
    
    # Profile
    profile_picture = models.ImageField(upload_to='students/profiles/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='students/covers/', null=True, blank=True)
    
    # Statistics (Added missing field)
    total_courses_enrolled = models.IntegerField(default=0)
    total_courses_completed = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Metadata
    registration_date = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    email_subscription = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.full_name} ({self.user.username})"
    
    def get_age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def update_statistics(self):
        """Update student statistics"""
        self.total_courses_enrolled = self.enrollments.count()
        self.total_courses_completed = self.enrollments.filter(enrollment_status='completed').count()
        
        # Calculate total points from completed lessons
        from django.db.models import Sum
        total_points = StudentLessonProgress.objects.filter(
            student=self,
            status='completed'
        ).aggregate(total=Sum('points_earned'))['total'] or 0
        self.total_points = total_points
        self.save()

# ==================== MODULE MODEL ====================
class Module(models.Model):
    """Learning module containing lessons"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    
    # Module details (Added missing title field)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    duration_minutes = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    
    # Requirements
    required_completion_percentage = models.IntegerField(default=0)
    unlock_days_after_enrollment = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.order}. {self.title}"
    
    def get_total_lessons(self):
        return self.lessons.count()
    
    def get_total_duration(self):
        from django.db.models import Sum
        return self.lessons.aggregate(total=models.Sum('duration_minutes'))['total'] or 0
    
    def get_completed_lessons_count(self, student):
        """Get number of lessons completed by a specific student"""
        return StudentLessonProgress.objects.filter(
            student=student,
            lesson__module=self,
            status='completed'
        ).count()

# ==================== LESSON MODEL ====================
class Lesson(models.Model):
    LESSON_TYPES = [
        ('video', 'Video Lesson'),
        ('article', 'Text Article'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('live_session', 'Live Session'),
        ('download', 'Downloadable Content'),
    ]
    
    VIDEO_SOURCES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('wistia', 'Wistia'),
        ('custom', 'Custom URL'),
        ('upload', 'Uploaded Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    
    # Lesson details
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='video')
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)  # For articles/HTML content
    
    # Video settings
    video_source = models.CharField(max_length=20, choices=VIDEO_SOURCES, default='youtube', blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to=lesson_video_path, null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    
    # Requirements and settings
    order = models.IntegerField(default=0)
    is_free = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    require_completion = models.BooleanField(default=True)
    points_value = models.IntegerField(default=10)
    
    # Interactive features
    enable_comments = models.BooleanField(default=True)
    enable_download = models.BooleanField(default=False)
    
    # Resources
    attached_files = models.FileField(upload_to='lessons/files/', null=True, blank=True)
    external_resources = models.TextField(blank=True)  # JSON or text list
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.module.course.slug}-module-{self.module.order}-lesson-{self.order}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.module.order}.{self.order} {self.title}"
    
    def get_youtube_id(self):
        """Extract YouTube video ID from URL"""
        if not self.video_url or 'youtube' not in self.video_url:
            return None
        import re
        pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(pattern, self.video_url)
        return match.group(1) if match else None
    
    def get_embed_url(self):
        """Get embed URL for video"""
        if self.video_source == 'youtube' and self.get_youtube_id():
            return f'https://www.youtube.com/embed/{self.get_youtube_id()}'
        elif self.video_source == 'vimeo':
            # Extract Vimeo ID
            import re
            pattern = r'vimeo\.com\/(\d+)'
            match = re.search(pattern, self.video_url)
            if match:
                return f'https://player.vimeo.com/video/{match.group(1)}'
        return self.video_url
    
    def get_next_lesson(self):
        """Get the next lesson in the module"""
        try:
            return Lesson.objects.filter(
                module=self.module,
                order__gt=self.order,
                is_published=True
            ).order_by('order').first()
        except:
            return None
    
    def get_previous_lesson(self):
        """Get the previous lesson in the module"""
        try:
            return Lesson.objects.filter(
                module=self.module,
                order__lt=self.order,
                is_published=True
            ).order_by('-order').first()
        except:
            return None

# ==================== QUIZ MODEL ====================
class Quiz(models.Model):
    QUIZ_TYPES = [
        ('practice', 'Practice Quiz'),
        ('module', 'Module Quiz'),
        ('final', 'Final Exam'),
        ('assessment', 'Assessment'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz', null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes', null=True, blank=True)
    
    # Quiz details
    title = models.CharField(max_length=200, blank=True)  # Added title field
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=20, choices=QUIZ_TYPES, default='practice')
    
    # Settings
    duration_minutes = models.IntegerField(default=30)
    passing_score = models.IntegerField(default=80)
    max_attempts = models.IntegerField(default=3)
    show_correct_answers = models.BooleanField(default=True)
    randomize_questions = models.BooleanField(default=True)
    require_passing = models.BooleanField(default=False)
    
    # Grading
    total_points = models.IntegerField(default=100)
    weight_percentage = models.IntegerField(default=0)  # For final grade calculation
    
    # Status
    is_published = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        # Get title from related objects
        title = self.title
        if not title and self.lesson:
            title = self.lesson.title
        elif not title and self.module:
            title = self.module.title
        elif not title and self.course:
            title = self.course.name
        
        return f"Quiz: {title} ({self.get_quiz_type_display()})"
    
    def get_question_count(self):
        return self.questions.count()
    
    def get_total_duration(self):
        return self.duration_minutes
    
    def save(self, *args, **kwargs):
        # Auto-generate title if not provided
        if not self.title:
            if self.lesson:
                self.title = f"Quiz: {self.lesson.title}"
            elif self.module:
                self.title = f"Module Quiz: {self.module.title}"
            elif self.course:
                self.title = f"Final Exam: {self.course.name}"
        super().save(*args, **kwargs)

# ==================== QUIZ QUESTION MODEL ====================
class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('mcq_single', 'Multiple Choice (Single)'),
        ('mcq_multiple', 'Multiple Choice (Multiple)'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('matching', 'Matching'),
        ('fill_blank', 'Fill in the Blanks'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    # Question details
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq_single')
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.IntegerField(default=10)
    order = models.IntegerField(default=0)
    
    # Options for MCQ (store as JSON)
    options = models.JSONField(default=list, blank=True)
    correct_answers = models.JSONField(default=list, blank=True)
    
    # Media
    image = models.ImageField(upload_to='quiz/questions/', null=True, blank=True)
    audio = models.FileField(upload_to='quiz/audio/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
    
    def check_answer(self, user_answer):
        """Check if user's answer is correct"""
        if self.question_type == 'mcq_single':
            return str(user_answer) in [str(ans) for ans in self.correct_answers]
        elif self.question_type == 'mcq_multiple':
            # For multiple correct answers, all must be selected
            user_answers = set(str(ans) for ans in user_answer)
            correct_answers = set(str(ans) for ans in self.correct_answers)
            return user_answers == correct_answers
        elif self.question_type == 'true_false':
            return str(user_answer).lower() == str(self.correct_answers[0]).lower()
        # For other types, manual grading required
        return False

# ==================== ENROLLMENT MODEL ====================
class Enrollment(models.Model):
    ENROLLMENT_STATUS = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid'),
        ('refunded', 'Refunded'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment Details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    enrollment_status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Progress Tracking
    progress_percentage = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    total_time_spent = models.IntegerField(default=0)  # in minutes
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_issue_date = models.DateField(null=True, blank=True)
    certificate_id = models.CharField(max_length=100, blank=True)
    
    # Payment Details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    final_grade = models.CharField(max_length=10, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.name}"
    
    def is_active(self):
        return self.enrollment_status == 'active'
    
    def calculate_end_date(self):
        """Calculate end date based on course access duration"""
        if self.start_date:
            from datetime import timedelta
            return self.start_date + timedelta(days=self.course.access_duration_days)
        return None
    
    def time_remaining(self):
        """Get days remaining until enrollment expires"""
        if self.end_date:
            from datetime import date
            remaining = (self.end_date - date.today()).days
            return max(0, remaining)
        return None
    
    def update_progress(self):
        """Update progress percentage"""
        total_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_published=True,
            require_completion=True
        ).count()
        
        if total_lessons == 0:
            self.progress_percentage = 0
        else:
            completed_lessons = StudentLessonProgress.objects.filter(
                student=self.student,
                lesson__module__course=self.course,
                status='completed',
                enrollment=self
            ).count()
            self.progress_percentage = (completed_lessons / total_lessons) * 100
        
        # Update enrollment status based on progress
        if self.progress_percentage >= 100:
            self.enrollment_status = 'completed'
            if not self.completed_at:
                self.completed_at = timezone.now()
        
        self.save()
        return self.progress_percentage

# ==================== STUDENT COURSE PROGRESS MODEL ====================
class StudentCourseProgress(models.Model):
    """Tracks overall progress for a student in a course"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='student_progress')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='course_progress', null=True)
    
    # Progress tracking
    overall_progress = models.FloatField(default=0.0)
    completed_lessons = models.IntegerField(default=0)
    total_lessons = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    
    # Time tracking
    total_time_spent = models.IntegerField(default=0)  # in minutes
    last_accessed = models.DateTimeField(auto_now=True)
    first_accessed = models.DateTimeField(auto_now_add=True)
    
    # Module progress (store as JSON)
    module_progress = models.JSONField(default=dict, blank=True)
    
    # Completion
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Grade
    final_grade = models.CharField(max_length=10, blank=True)
    quiz_average = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['student', 'course', 'enrollment']
        verbose_name_plural = 'Student Course Progress'
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.name} ({self.overall_progress}%)"
    
    def update_progress(self):
        """Update overall progress based on completed lessons"""
        from django.db.models import Sum
        
        # Count total required lessons
        self.total_lessons = Lesson.objects.filter(
            module__course=self.course,
            is_published=True,
            require_completion=True
        ).count()
        
        # Count completed lessons
        self.completed_lessons = StudentLessonProgress.objects.filter(
            student=self.student,
            lesson__module__course=self.course,
            status='completed',
            enrollment=self.enrollment
        ).count()
        
        # Calculate percentage
        if self.total_lessons > 0:
            self.overall_progress = (self.completed_lessons / self.total_lessons) * 100
        
        # Check if course is completed
        if self.overall_progress >= 100:
            self.is_completed = True
            if not self.completed_at:
                self.completed_at = timezone.now()
        
        # Calculate total points earned
        self.total_points = StudentLessonProgress.objects.filter(
            student=self.student,
            lesson__module__course=self.course,
            status='completed',
            enrollment=self.enrollment
        ).aggregate(total=Sum('points_earned'))['total'] or 0
        
        # Calculate module progress
        modules = Module.objects.filter(course=self.course, is_published=True)
        module_data = {}
        for module in modules:
            total_module_lessons = module.lessons.filter(
                is_published=True, 
                require_completion=True
            ).count()
            completed_module_lessons = StudentLessonProgress.objects.filter(
                student=self.student,
                lesson__module=module,
                status='completed',
                enrollment=self.enrollment
            ).count()
            
            module_progress = 0
            if total_module_lessons > 0:
                module_progress = (completed_module_lessons / total_module_lessons) * 100
            
            module_data[str(module.id)] = {
                'title': module.title,
                'progress': module_progress,
                'completed': completed_module_lessons,
                'total': total_module_lessons
            }
        
        self.module_progress = module_data
        self.save()
        
        # Update enrollment progress
        if self.enrollment:
            self.enrollment.progress_percentage = self.overall_progress
            if self.is_completed and not self.enrollment.completed_at:
                self.enrollment.completed_at = self.completed_at
                self.enrollment.enrollment_status = 'completed'
            self.enrollment.save()
        
        return self.overall_progress

# ==================== STUDENT LESSON PROGRESS MODEL ====================
class StudentLessonProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progress', null=True)
    
    # Progress tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    # Video-specific tracking
    video_progress_seconds = models.IntegerField(default=0)
    video_total_watched = models.IntegerField(default=0)  # Total seconds watched
    
    # Points and scores
    points_earned = models.IntegerField(default=0)
    quiz_score = models.IntegerField(null=True, blank=True)
    
    # Attempts
    attempts_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'lesson', 'enrollment']
        ordering = ['lesson__module__order', 'lesson__order']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.title} ({self.status})"
    
    def mark_as_completed(self, save=True):
        """Mark lesson as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if not self.started_at:
            self.started_at = timezone.now()
        
        # Award points
        self.points_earned = self.lesson.points_value
        
        if save:
            self.save()
        
        # Update enrollment and course progress
        if self.enrollment:
            self.enrollment.update_progress()
            
            # Update StudentCourseProgress
            course_progress, created = StudentCourseProgress.objects.get_or_create(
                student=self.student,
                course=self.lesson.module.course,
                enrollment=self.enrollment,
                defaults={
                    'overall_progress': 0,
                    'total_lessons': 0,
                    'completed_lessons': 0
                }
            )
            course_progress.update_progress()
        
        return self

# ==================== STUDENT QUIZ ATTEMPT MODEL ====================
class StudentQuizAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='quiz_attempts', null=True)
    
    # Attempt details
    attempt_number = models.IntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(default=0)
    
    # Results
    score = models.FloatField(default=0.0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    skipped_questions = models.IntegerField(default=0)
    
    # Status
    is_completed = models.BooleanField(default=False)
    is_passed = models.BooleanField(default=False)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = ['student', 'quiz', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.quiz} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        """Calculate final score"""
        total_points = 0
        earned_points = 0
        
        for response in self.responses.all():
            total_points += response.question.points
            if response.is_correct:
                earned_points += response.question.points
        
        if total_points > 0:
            self.score = (earned_points / total_points) * 100
        else:
            self.score = 0
        
        self.is_passed = self.score >= self.quiz.passing_score
        self.is_completed = True
        self.submitted_at = timezone.now()
        self.save()
        return self.score

# ==================== QUIZ RESPONSE MODEL ====================
class QuizResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(StudentQuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='responses')
    
    # Response data (store as JSON for flexibility)
    answer_data = models.JSONField(default=dict)
    text_response = models.TextField(blank=True)
    
    # Grading
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    feedback = models.TextField(blank=True)
    
    # Timing
    time_spent_seconds = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        return f"Response to Q{self.question.order} in Attempt {self.attempt.attempt_number}"
    
    def grade_response(self):
        """Grade the response"""
        if self.question.question_type in ['mcq_single', 'mcq_multiple', 'true_false']:
            self.is_correct = self.question.check_answer(self.answer_data)
            if self.is_correct:
                self.points_earned = self.question.points
            else:
                self.points_earned = 0
        elif self.question.question_type == 'short_answer':
            # For short answer, auto-grade if exact match is in correct answers
            user_answer = str(self.text_response).strip().lower()
            correct_answers = [str(ans).strip().lower() for ans in self.question.correct_answers]
            self.is_correct = user_answer in correct_answers
            if self.is_correct:
                self.points_earned = self.question.points
            else:
                self.points_earned = 0
        else:
            # Essay and other types require manual grading
            self.is_correct = False
            self.points_earned = 0
        
        self.save()
        return self.is_correct

# ==================== PAYMENT MODEL ====================
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit/Debit Card'),
        ('cod', 'Cash on Delivery'),
        ('free', 'Free'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=200, unique=True)
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    is_verified = models.BooleanField(default=False)
    
    # Metadata
    payment_date = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Gateway Response
    gateway_response = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment {self.transaction_id} - ৳{self.amount}"
    
    def verify_payment(self, user=None):
        """Verify payment and update enrollment"""
        self.is_verified = True
        self.status = 'completed'
        self.verified_at = timezone.now()
        if user:
            self.verified_by = user
        self.save()
        
        # Update enrollment
        self.enrollment.payment_status = 'paid'
        self.enrollment.enrollment_status = 'active'
        self.enrollment.start_date = timezone.now().date()
        self.enrollment.end_date = self.enrollment.calculate_end_date()
        self.enrollment.amount_paid = self.amount
        self.enrollment.save()
        
        # Update student statistics
        self.student.total_courses_enrolled = self.student.enrollments.count()
        self.student.save()
        
        # Update course statistics
        self.enrollment.course.total_enrollments = self.enrollment.course.enrollments.filter(
            enrollment_status='active'
        ).count()
        self.enrollment.course.save()
        
        return True

# ==================== CERTIFICATE MODEL ====================
class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    
    # Certificate Details
    certificate_id = models.CharField(max_length=100, unique=True)
    certificate_url = models.URLField(blank=True)
    issued_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Content
    student_name = models.CharField(max_length=200)
    course_name = models.CharField(max_length=200)
    completion_date = models.DateField()
    grade = models.CharField(max_length=20, blank=True)
    final_score = models.FloatField(null=True, blank=True)
    
    # Verification
    verification_code = models.CharField(max_length=50, unique=True)
    is_verified = models.BooleanField(default=True)
    
    # Template
    template = models.CharField(max_length=100, default='default')
    background_image = models.ImageField(upload_to='certificates/backgrounds/', null=True, blank=True)
    
    # Digital Signature
    signed_by = models.CharField(max_length=200, blank=True)
    signature_image = models.ImageField(upload_to='certificates/signatures/', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    downloaded_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student_name}"
    
    def generate_certificate_id(self):
        """Generate unique certificate ID"""
        import random
        import string
        if not self.certificate_id:
            prefix = "CERT"
            timestamp = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.certificate_id = f"{prefix}-{timestamp}-{random_str}"
        return self.certificate_id
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.generate_certificate_id()
        if not self.verification_code:
            import random
            import string
            self.verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        super().save(*args, **kwargs)
    
    def get_verification_url(self):
        return f"/verify-certificate/{self.verification_code}/"

# ==================== COURSE RESOURCE MODEL ====================
class CourseResource(models.Model):
    RESOURCE_TYPES = [
        ('pdf', 'PDF Document'),
        ('video', 'Video File'),
        ('audio', 'Audio File'),
        ('image', 'Image'),
        ('link', 'External Link'),
        ('document', 'Document'),
        ('presentation', 'Presentation'),
        ('spreadsheet', 'Spreadsheet'),
        ('zip', 'Zip Archive'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    
    # Resource details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    
    # File or URL
    file = models.FileField(upload_to=resource_file_path, null=True, blank=True)
    url = models.URLField(blank=True)
    
    # Access control
    is_free = models.BooleanField(default=False)
    available_after_days = models.IntegerField(default=0)
    
    # Metadata
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"
    
    def get_file_size(self):
        if self.file and self.file.size:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "0 B"

# ==================== COURSE REVIEW MODEL ====================
class CourseReview(models.Model):
    RATING_CHOICES = [
        (1, '★☆☆☆☆'),
        (2, '★★☆☆☆'),
        (3, '★★★☆☆'),
        (4, '★★★★☆'),
        (5, '★★★★★'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    
    # Review content
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Verification
    is_verified = models.BooleanField(default=False)
    is_helpful = models.BooleanField(default=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.rating}★ for {self.course.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update course average rating
        reviews = CourseReview.objects.filter(course=self.course, is_published=True)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.course.average_rating = round(avg_rating, 1)
            self.course.review_count = reviews.count()
            self.course.save()

# ==================== COUPON MODEL ====================
class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free', '100% Off'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Usage limits
    usage_limit = models.IntegerField(default=100)
    used_count = models.IntegerField(default=0)
    per_user_limit = models.IntegerField(default=1)
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Applicability
    applicable_courses = models.ManyToManyField(Course, blank=True, related_name='coupons')
    minimum_cart_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percentage' else '৳'})"
    
    def is_valid(self, user=None, course=None):
        """Check if coupon is valid for use"""
        now = timezone.now()
        
        if not self.is_active:
            return False, "Coupon is not active"
        
        if now < self.valid_from:
            return False, "Coupon is not yet valid"
        
        if now > self.valid_until:
            return False, "Coupon has expired"
        
        if self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        if user:
            user_usage = Enrollment.objects.filter(
                student__user=user,
                payments__transaction_id__contains=self.code
            ).count()
            if user_usage >= self.per_user_limit:
                return False, "You have already used this coupon"
        
        return True, "Coupon is valid"
    
    def calculate_discount(self, amount):
        """Calculate discount amount"""
        if self.discount_type == 'percentage':
            discount = (amount * self.discount_value) / 100
        elif self.discount_type == 'fixed':
            discount = min(self.discount_value, amount)
        else:  # free
            discount = amount
        
        return Decimal(discount)

# ==================== NOTIFICATION MODEL ====================
class Notification(models.Model):
    TYPES = [
        ('enrollment', 'New Enrollment'),
        ('completion', 'Course Completion'),
        ('payment', 'Payment Received'),
        ('certificate', 'Certificate Issued'),
        ('reminder', 'Reminder'),
        ('announcement', 'Announcement'),
        ('promotion', 'Promotion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Content
    notification_type = models.CharField(max_length=20, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    
    # Related objects
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

# ==================== BLOG POST MODEL ====================
class BlogPost(models.Model):
    CATEGORIES = [
        ('islamic_knowledge', 'Islamic Knowledge'),
        ('quran_studies', 'Quran Studies'),
        ('sunnah', 'Sunnah & Hadith'),
        ('student_life', 'Student Life'),
        ('announcements', 'Announcements'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Content
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=300)
    
    # Categorization
    category = models.CharField(max_length=50, choices=CATEGORIES)
    tags = models.CharField(max_length=200, blank=True)
    
    # Author
    author = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='blog_thumbnails/', null=True, blank=True)
    
    # Status
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Analytics
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

# ==================== GALLERY MODEL ====================
class Gallery(models.Model):
    CATEGORIES = [
        ('classroom', 'Classroom Sessions'),
        ('events', 'Events & Seminars'),
        ('students', 'Student Activities'),
        ('teachers', 'Teacher Portfolios'),
        ('campus', 'Campus Life'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Image Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    
    # Image
    image = models.ImageField(upload_to='gallery/')
    thumbnail = models.ImageField(upload_to='gallery/thumbnails/', null=True, blank=True)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    
    # Student/Event Association
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.title

# ==================== DONATION MODEL ====================
class Donation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Donor Information
    donor_name = models.CharField(max_length=200)
    donor_email = models.EmailField()
    donor_phone = models.CharField(max_length=20)
    
    # Donation Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Payment.PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True)
    
    # Purpose
    purpose = models.CharField(max_length=200, blank=True)
    is_zakat = models.BooleanField(default=False)
    is_sadaqah = models.BooleanField(default=False)
    is_project_specific = models.BooleanField(default=False)
    project_name = models.CharField(max_length=200, blank=True)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    
    # Metadata
    donated_at = models.DateTimeField(auto_now_add=True)
    receipt_sent = models.BooleanField(default=False)
    
    # Acknowledgement
    acknowledgement_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Donation from {self.donor_name} - {self.amount} BDT"

# ==================== FAQ MODEL ====================
class FAQ(models.Model):
    CATEGORIES = [
        ('admission', 'Admission & Enrollment'),
        ('courses', 'Courses & Curriculum'),
        ('payment', 'Payment & Fees'),
        ('technical', 'Technical Support'),
        ('general', 'General Questions'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Question & Answer
    question = models.CharField(max_length=500)
    answer = models.TextField()
    
    # Categorization
    category = models.CharField(max_length=50, choices=CATEGORIES)
    language = models.CharField(max_length=20, default='bangla')
    
    # Ordering
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'category']
    
    def __str__(self):
        return self.question[:100]

# ==================== CONTACT MESSAGE MODEL ====================
class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('admission', 'Admission Query'),
        ('payment', 'Payment Issue'),
        ('technical', 'Technical Support'),
        ('feedback', 'Feedback/Suggestion'),
        ('complaint', 'Complaint'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Sender Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Message Details
    subject_type = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    is_read = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Metadata
    received_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Response
    response_sent = models.BooleanField(default=False)
    response_notes = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Related Objects
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.get_status_display()})"
    
    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
    
    def mark_as_resolved(self, user=None):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if user:
            self.responded_by = user
            self.responded_at = timezone.now()
        self.save()
    
    def send_response_email(self, response_text, user=None):
        """Send response email to the contact message sender"""
        try:
            send_mail(
                subject=f'Re: {self.subject} - Taw Haa Zin Nurain Online Madarasa',
                message=f'''Assalamu Alaikum {self.name},

Thank you for contacting Taw Haa Zin Nurain Online Madarasa.

Regarding your message:
"{self.message[:100]}..."

Our Response:
{response_text}

If you have any further questions, please don't hesitate to contact us.

Best regards,
Taw Haa Zin Nurain Online Madarasa
Contact: +8801740433580''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                fail_silently=False,
            )
            
            self.response_sent = True
            self.response_notes = response_text
            if user:
                self.responded_by = user
            self.responded_at = timezone.now()
            self.save()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def get_time_since_received(self):
        """Get human-readable time since message was received"""
        delta = timezone.now() - self.received_at
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

            