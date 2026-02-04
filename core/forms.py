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
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone', 'address', 
            'city', 'country', 'occupation', 'education_level', 'about_me',
            'preferred_language', 'profile_picture', 'cover_photo'
        ]
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
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default values safely
        self.fields['country'].initial = 'Bangladesh'
        self.fields['preferred_language'].initial = 'en'

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



# forms.py - Update the StudentUpdateForm
class StudentUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text="Optional. Must be at least 10 years old.",
        required=False
    )
    
    class Meta:
        model = Student
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone', 'address', 
            'city', 'country', 'occupation', 'education_level', 'about_me',
            'preferred_language', 'profile_picture', 'cover_photo'
        ]
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
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values
        self.fields['preferred_language'].initial = 'en'
        self.fields['country'].initial = 'Bangladesh'
        
        # Make fields required/optional
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
        
        # These fields have defaults, so they're not required
        self.fields['preferred_language'].required = False
        self.fields['country'].required = False
        
        # Remove timezone field reference if it exists in HTML
        if 'timezone' in self.fields:
            del self.fields['timezone']
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure defaults are set if fields are empty
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


