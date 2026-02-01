from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Main Models
class Course(models.Model):
    COURSE_CATEGORIES = [
        ('quran', 'Authentic Quran Recitations'),
        ('tadabbur', 'Tadabbur Quran'),
        ('sirah', 'Riratunnabi (SM)'),
        ('aqida', 'Aqida Learning Courses'),
        ('other', 'Other Islamic Studies'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=COURSE_CATEGORIES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    description = models.TextField()
    short_description = models.CharField(max_length=300)
    
    # Pricing
    base_fee = models.DecimalField(max_digits=10, decimal_places=2)  # 1000-3000 BDT
    discount_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Course Details
    duration_weeks = models.IntegerField()
    classes_per_week = models.IntegerField()
    class_duration_minutes = models.IntegerField()
    
    # Timing Slots
    morning_slot = models.BooleanField(default=False)
    afternoon_slot = models.BooleanField(default=False)
    evening_slot = models.BooleanField(default=False)
    night_slot = models.BooleanField(default=False)
    
    # Prerequisites
    min_age = models.IntegerField(default=10)
    prerequisites = models.TextField(blank=True)
    
    # Resources
    materials_included = models.BooleanField(default=True)
    additional_books = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    max_students = models.IntegerField(default=50)
    current_enrollment = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    enrollment_deadline = models.DateField()
    
    # Images
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    featured_image = models.ImageField(upload_to='course_images/', null=True, blank=True)
    
    def enrollment_percentage(self):
        if self.max_students > 0:
            return (self.current_enrollment / self.max_students) * 100
        return 0
    
    def is_available(self):
        return self.is_active and self.current_enrollment < self.max_students
    
    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"

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
    title = models.CharField(max_length=100)
    bio = models.TextField()
    specialization = models.CharField(max_length=200)
    
    # Professional Details
    role = models.CharField(max_length=20, choices=ROLES)
    experience_years = models.IntegerField()
    qualifications = models.TextField()
    
    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Social Media
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    # Images
    profile_picture = models.ImageField(upload_to='instructor_profiles/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    courses = models.ManyToManyField(Course, related_name='instructors', blank=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    
    OCCUPATION_CHOICES = [
        ('student', 'Student'),
        ('professional', 'Professional'),
        ('housewife', 'Housewife'),
        ('business', 'Business'),
        ('other', 'Other'),
    ]
    
    EDUCATION_CHOICES = [
        ('school', 'School Student'),
        ('college', 'College Student'),
        ('university', 'University Student'),
        ('madrasa', 'Madrasa Student'),
        ('graduate', 'Graduate'),
        ('post_graduate', 'Post Graduate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    # Background
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES)
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES)
    previous_islamic_studies = models.TextField(blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=50, blank=True, default='Bangla')
    
    # Status
    is_active = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    
    # Profile
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def __str__(self):
        return f"{self.full_name} - {self.phone}"

class Enrollment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partial Payment'),
        ('paid', 'Fully Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    ENROLLMENT_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment Details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    expected_end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    
    # Payment Details
    course_fee = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    enrollment_status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='active')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Progress Tracking
    attendance_percentage = models.FloatField(default=0)
    assignment_completion = models.FloatField(default=0)
    overall_progress = models.FloatField(default=0)
    
    # Class Details
    assigned_instructor = models.ForeignKey(Instructor, on_delete=models.SET_NULL, null=True, blank=True)
    class_time_slot = models.CharField(max_length=100)
    
    # Metadata
    is_installment = models.BooleanField(default=False)
    installment_count = models.IntegerField(default=1)
    next_installment_date = models.DateField(null=True, blank=True)
    
    # Completion Tracking
    completion_certificate_issued = models.BooleanField(default=False)
    certificate_issue_date = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def update_progress(self):
        # Calculate progress based on attendance and assignments
        self.overall_progress = (self.attendance_percentage + self.assignment_completion) / 2
        self.save()
    
    def check_completion(self):
        if self.overall_progress >= 80 and not self.completion_certificate_issued:
            self.enrollment_status = 'completed'
            self.actual_end_date = timezone.now().date()
            self.completion_certificate_issued = True
            self.certificate_issue_date = timezone.now().date()
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.name}"

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('rocket', 'Rocket'),
        ('bank', 'Bank Transfer'),
        ('cash', 'Cash'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='payments')
    
    # Payment Details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, unique=True)
    
    # Installment Info
    installment_number = models.IntegerField(default=1)
    is_installment = models.BooleanField(default=False)
    
    # Status
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    payment_date = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Reference
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def verify_payment(self, user):
        self.is_verified = True
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save()
        
        # Update enrollment payment status
        enrollment = self.enrollment
        enrollment.total_paid += self.amount
        enrollment.due_amount = enrollment.course_fee - enrollment.total_paid
        
        if enrollment.due_amount <= 0:
            enrollment.payment_status = 'paid'
        elif enrollment.total_paid > 0:
            enrollment.payment_status = 'partial'
        
        enrollment.save()
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} BDT"

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
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    
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
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

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

class Office(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Office Details
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    
    # Location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Status
    is_main_office = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Office Hours
    opening_hours = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.city}"

class Notification(models.Model):
    TYPES = [
        ('payment_reminder', 'Payment Reminder'),
        ('class_reminder', 'Class Reminder'),
        ('assignment_due', 'Assignment Due'),
        ('course_completion', 'Course Completion'),
        ('general', 'General Announcement'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Recipient
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=TYPES)
    
    # Related Objects
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    send_email = models.BooleanField(default=False)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Action
    action_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"
    
# Add to your existing models.py
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
    
    # Metadata
    received_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Response
    response_sent = models.BooleanField(default=False)
    response_notes = models.TextField(blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Priority
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Related Objects (if applicable)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-received_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def mark_as_read(self, user=None):
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
    
    def __str__(self):
        return f"{self.name} - {self.subject} ({self.get_status_display()})"





