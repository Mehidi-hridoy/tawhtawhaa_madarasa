from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *



class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, label='First Name')
    last_name = forms.CharField(max_length=30, required=True, label='Last Name')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Help texts
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = '''
        <ul class="small text-muted">
            <li>Your password can\'t be too similar to your other personal information.</li>
            <li>Your password must contain at least 8 characters.</li>
            <li>Your password can\'t be a commonly used password.</li>
            <li>Your password can\'t be entirely numeric.</li>
        </ul>
        '''
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

class StudentRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Must be at least 10 years old",
        required=True
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label='I accept the terms and conditions',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Student
        exclude = ['user', 'is_active', 'registration_date', 'student_id']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801XXXXXXXXX'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'education': forms.Select(attrs={'class': 'form-select'}),
            'previous_islamic_studies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 
                                                            'placeholder': 'Briefly describe any previous Islamic studies experience...'}),
            'preferred_time_slot': forms.Select(attrs={'class': 'form-select'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add country choices
        self.fields['country'].initial = 'Bangladesh'
        # Add required attribute to necessary fields
        self.fields['full_name'].required = True
        self.fields['gender'].required = True
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
        help_text="Must be at least 10 years old",
        required=False
    )
    
    class Meta:
        model = Student
        exclude = ['user', 'is_active', 'registration_date', 'student_id']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'education': forms.Select(attrs={'class': 'form-select'}),
            'previous_islamic_studies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'preferred_time_slot': forms.Select(attrs={'class': 'form-select'}),
            'preferred_language': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
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
        fields = ['class_time_slot', 'is_installment', 'installment_count']
        widgets = {
            'class_time_slot': forms.Select(attrs={'class': 'form-select'}),
            'is_installment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installment_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1, 
                'max': 12,
                'placeholder': 'Number of installments'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamic time slot choices based on course availability
        self.fields['class_time_slot'].label = 'Preferred Class Time'
        
        # Add help texts
        self.fields['is_installment'].help_text = 'Check if you want to pay in installments'
        self.fields['installment_count'].help_text = 'Number of installments (1-12)'

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
        fields = ['amount', 'payment_method', 'transaction_id', 'reference_number', 'notes']
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
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Reference/Check Number (if applicable)'
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
            self.fields['amount'].initial = self.enrollment.due_amount
            self.fields['amount'].help_text = f'Due amount: ৳{self.enrollment.due_amount}'
        
        # Add placeholders and help texts
        self.fields['transaction_id'].help_text = 'Required for bKash/Nagad/Rocket payments'
        self.fields['reference_number'].help_text = 'Optional for bank transfers'
        
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.enrollment and amount > self.enrollment.due_amount:
            raise forms.ValidationError(f"Amount cannot exceed due amount of ৳{self.enrollment.due_amount}")
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
        exclude = ['created_at', 'updated_at', 'current_enrollment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'base_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_weeks': forms.NumberInput(attrs={'class': 'form-control'}),
            'classes_per_week': forms.NumberInput(attrs={'class': 'form-control'}),
            'class_duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'prerequisites': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'additional_books': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'enrollment_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'morning_slot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'afternoon_slot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'evening_slot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'night_slot': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'materials_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
        fields = ['question', 'answer', 'category', 'language', 'display_order', 'is_active']
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
        exclude = ['user']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'courses': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

class GalleryForm(forms.ModelForm):
    """Form for adding gallery items"""
    class Meta:
        model = Gallery
        fields = ['title', 'description', 'category', 'image', 'thumbnail', 'is_featured', 'student', 'course', 'event_date']
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


        