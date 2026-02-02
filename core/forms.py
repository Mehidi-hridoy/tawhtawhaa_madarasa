from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *
from datetime import date
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    phone = forms.CharField(max_length=20, required=False, label='Phone Number')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields.values():
            if field.widget.__class__.__name__ != 'CheckboxInput':
                field.widget.attrs.update({'class': 'form-control'})
        
        # Customize help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['email'].help_text = 'Required. We\'ll send important notifications to this email.'
        self.fields['phone'].help_text = 'Optional but recommended for important updates.'
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class StudentRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Optional. Must be at least 10 years old.",
        required=False
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label='I accept the terms and conditions',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Student
        exclude = ['user', 'is_active', 'registration_date', 'email_verified', 'phone_verified',
                  'total_courses_enrolled', 'total_courses_completed', 'total_learning_hours',
                  'streak_days', 'last_active', 'email_subscription']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bangladesh'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'education_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., B.Sc in Computer Science'}),
            'about_me': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Tell us about yourself...'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values
        self.fields['country'].initial = 'Bangladesh'
        self.fields['preferred_language'].initial = 'en'
        self.fields['timezone'].initial = 'Asia/Dhaka'
        
        # Make required fields
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 10:
                raise forms.ValidationError("You must be at least 10 years old to register.")
        return dob

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class StudentUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Optional. Must be at least 10 years old.",
        required=False
    )
    
    class Meta:
        model = Student
        exclude = ['user', 'is_active', 'registration_date', 'email_verified', 'phone_verified',
                  'total_courses_enrolled', 'total_courses_completed', 'total_learning_hours',
                  'streak_days', 'last_active', 'email_subscription']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'education_level': forms.TextInput(attrs={'class': 'form-control'}),
            'about_me': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        self.fields['timezone'].initial = 'Asia/Dhaka'
        self.fields['preferred_language'].initial = 'en'
        self.fields['country'].initial = 'Bangladesh'
        
        # Make fields required/optional
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
        
        # These fields have defaults, so they're not required
        self.fields['timezone'].required = False
        self.fields['preferred_language'].required = False
        self.fields['country'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure defaults are set if fields are empty
        if not cleaned_data.get('timezone'):
            cleaned_data['timezone'] = 'Asia/Dhaka'
        if not cleaned_data.get('preferred_language'):
            cleaned_data['preferred_language'] = 'en'
        if not cleaned_data.get('country'):
            cleaned_data['country'] = 'Bangladesh'
        return cleaned_data
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 10:
                raise forms.ValidationError("You must be at least 10 years old.")
        return dob



class EnrollmentForm(forms.ModelForm):
    agree_to_terms = forms.BooleanField(
        required=True,
        label='I agree to the terms and conditions of enrollment',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Enrollment
        fields = []  # No specific fields needed as enrollment is automatic
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PaymentForm(forms.ModelForm):
    # Additional field for payment screenshot/attachment
    payment_proof = forms.FileField(
        required=False,
        label='Payment Proof (Screenshot/Receipt)',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*,.pdf'})
    )
    
    confirm_details = forms.BooleanField(
        required=True,
        label='I confirm that the payment details provided are correct',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01', 
                'min': '0',
                'placeholder': 'Amount in BDT'
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'bKash/Nagad/Rocket Transaction ID'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Any additional information about this payment...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.enrollment = kwargs.pop('enrollment', None)
        super().__init__(*args, **kwargs)
        
        if self.enrollment:
            # Set initial amount as due amount
            due_amount = self.enrollment.course.get_current_price() - self.enrollment.amount_paid
            self.fields['amount'].initial = due_amount
            self.fields['amount'].help_text = f'Due amount: ৳{due_amount}'
        
        # Add placeholders and help texts
        self.fields['transaction_id'].help_text = 'Required for bKash/Nagad/Rocket payments. Enter "auto" to generate automatically.'
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.enrollment:
            due_amount = self.enrollment.course.get_current_price() - self.enrollment.amount_paid
            if amount > due_amount:
                raise forms.ValidationError(f"Amount cannot exceed due amount of ৳{due_amount}")
        return amount

class DonationForm(forms.ModelForm):
    agree_to_terms = forms.BooleanField(
        required=True,
        label='I agree that this donation is for charitable purposes only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Donation
        fields = [
            'donor_name', 'donor_email', 'donor_phone', 'amount', 
            'payment_method', 'purpose', 'is_zakat', 'is_sadaqah',
            'is_project_specific', 'project_name', 'is_anonymous',
            'acknowledgement_message'
        ]
        widgets = {
            'donor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your full name'}),
            'donor_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
            'donor_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Amount in BDT'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Textarea(attrs={
                'rows': 2, 
                'class': 'form-control',
                'placeholder': 'Optional: Specific purpose for this donation'
            }),
            'project_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'If donating for a specific project'
            }),
            'acknowledgement_message': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Optional: Any message you want to include with your donation'
            }),
            'is_zakat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sadaqah': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_project_specific': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help texts
        self.fields['amount'].help_text = 'Minimum donation: ৳100'
        self.fields['is_anonymous'].help_text = 'Check if you want your donation to be anonymous'
        self.fields['is_zakat'].help_text = 'Check if this donation is Zakat'
        self.fields['is_sadaqah'].help_text = 'Check if this donation is Sadaqah'
        
        # Set initial values
        self.fields['is_sadaqah'].initial = True
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount < 100:
            raise forms.ValidationError("Minimum donation amount is ৳100")
        return amount

class ContactForm(forms.ModelForm):
    # Additional field for captcha or terms
    agree_to_privacy = forms.BooleanField(
        required=True,
        label='I agree to the privacy policy and terms of service',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject_type', 'subject', 'message', 'priority']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+8801XXXXXXXXX (optional)'
            }),
            'subject_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief subject of your message'
            }),
            'message': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Please provide detailed information about your inquiry...'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is logged in, pre-fill their information
        if self.user and self.user.is_authenticated:
            self.fields['name'].initial = self.user.get_full_name() or self.user.username
            self.fields['email'].initial = self.user.email
            
            if hasattr(self.user, 'student_profile'):
                self.fields['phone'].initial = self.user.student_profile.phone
        
        # Add help texts
        self.fields['priority'].help_text = 'Select the urgency of your inquiry'
        self.fields['subject_type'].help_text = 'What is your inquiry about?'
        
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise forms.ValidationError("Please provide more details in your message.")
        return message

class ResponseForm(forms.ModelForm):
    """Form for admin to respond to contact messages"""
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        label='Send response via email',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ContactMessage
        fields = ['status', 'response_notes', 'priority', 'is_important']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'response_notes': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Type your response here...'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'is_important': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['response_notes'].required = True
        self.fields['response_notes'].label = 'Response'

class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    class Meta:
        model = Course
        exclude = ['created_at', 'updated_at', 'published_at', 'created_by', 'enrollment_count',
                  'average_rating', 'review_count', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'course_type': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'price_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'learning_outcomes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'prerequisites': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'target_audience': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'base_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'estimated_duration_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'access_duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'promo_video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'certificate_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_completion_certificate': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_by'].initial = User.objects.first()  # Default to first user
    
    def clean(self):
        cleaned_data = super().clean()
        price_type = cleaned_data.get('price_type')
        base_price = cleaned_data.get('base_price')
        sale_price = cleaned_data.get('sale_price')
        
        if price_type == 'free' and base_price > 0:
            raise forms.ValidationError("Free courses must have base price of 0.")
        
        if sale_price and base_price and sale_price >= base_price:
            raise forms.ValidationError("Sale price must be less than base price.")
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    """Form for creating/editing categories"""
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'icon_class': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-book'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

class BlogPostForm(forms.ModelForm):
    """Form for creating/editing blog posts"""
    class Meta:
        model = BlogPost
        exclude = ['created_at', 'updated_at', 'published_at', 'views', 'likes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'comma,separated,tags'}),
            'author': forms.Select(attrs={'class': 'form-select'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

class FAQForm(forms.ModelForm):
    """Form for creating/editing FAQs"""
    class Meta:
        model = FAQ
        fields = '__all__'
        widgets = {
            'question': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class InstructorForm(forms.ModelForm):
    """Form for creating/editing instructors"""
    class Meta:
        model = Instructor
        exclude = ['user', 'created_at', 'updated_at', 'total_courses', 'total_students', 'average_rating']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'specialization': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube': forms.URLInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class GalleryForm(forms.ModelForm):
    """Form for adding gallery items"""
    class Meta:
        model = Gallery
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class ModuleForm(forms.ModelForm):
    """Form for creating/editing modules"""
    class Meta:
        model = Module
        exclude = ['created_at', 'updated_at']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'required_completion_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'unlock_days_after_enrollment': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LessonForm(forms.ModelForm):
    """Form for creating/editing lessons"""
    class Meta:
        model = Lesson
        exclude = ['created_at', 'updated_at', 'published_at', 'slug']
        widgets = {
            'module': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control', 'id': 'content-editor'}),
            'video_source': forms.Select(attrs={'class': 'form-select'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_file': forms.FileInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_completion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'points_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'enable_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_download': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attached_files': forms.FileInput(attrs={'class': 'form-control'}),
            'external_resources': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class QuizForm(forms.ModelForm):
    """Form for creating/editing quizzes"""
    class Meta:
        model = Quiz
        exclude = ['created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'quiz_type': forms.Select(attrs={'class': 'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'show_correct_answers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'randomize_questions': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_passing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'total_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'weight_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'available_until': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class QuizQuestionForm(forms.ModelForm):
    """Form for creating/editing quiz questions"""
    class Meta:
        model = QuizQuestion
        exclude = ['created_at', 'updated_at']
        widgets = {
            'quiz': forms.Select(attrs={'class': 'form-select'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'question_text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'audio': forms.FileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class QuestionOptionForm(forms.ModelForm):
    """Form for creating/editing question options"""
    class Meta:
        model = QuestionOption
        fields = '__all__'
        widgets = {
            'question': forms.Select(attrs={'class': 'form-select'}),
            'option_text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'explanation': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'match_text': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InteractiveMCQForm(forms.ModelForm):
    """Form for creating/editing interactive MCQs for videos"""
    class Meta:
        model = InteractiveMCQ
        fields = '__all__'
        widgets = {
            'lesson': forms.Select(attrs={'class': 'form-select'}),
            'question': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'appear_at_second': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_limit_seconds': forms.NumberInput(attrs={'class': 'form-control'}),
            'points_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_skip': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CourseResourceForm(forms.ModelForm):
    """Form for creating/editing course resources"""
    class Meta:
        model = CourseResource
        fields = '__all__'
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'available_after_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CourseReviewForm(forms.ModelForm):
    """Form for submitting course reviews"""
    class Meta:
        model = CourseReview
        fields = ['rating', 'title', 'content', 'is_helpful']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'is_helpful': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CouponForm(forms.ModelForm):
    """Form for creating/editing coupons"""
    class Meta:
        model = Coupon
        fields = '__all__'
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'usage_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'per_user_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_cart_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class CertificateForm(forms.ModelForm):
    """Form for creating/editing certificates"""
    class Meta:
        model = Certificate
        exclude = ['created_at', 'updated_at', 'verification_code', 'certificate_id']
        widgets = {
            'enrollment': forms.Select(attrs={'class': 'form-select'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'certificate_url': forms.URLInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'student_name': forms.TextInput(attrs={'class': 'form-control'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'final_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'signed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class OfficeForm(forms.ModelForm):
    """Form for creating/editing office locations"""
    class Meta:
        model = Office
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'is_main_office': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'opening_hours': forms.TextInput(attrs={'class': 'form-control'}),
        }


        