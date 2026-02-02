from .forms import UserUpdateForm, StudentUpdateForm, StudentRegistrationForm,UserRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404


# Authentication Views
def register(request):
    """User registration view"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        student_form = StudentRegistrationForm(request.POST)
        
        if user_form.is_valid() and student_form.is_valid():
            # Create user
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            # Create student profile
            student = student_form.save(commit=False)
            student.user = user
            student.save()
            
            # Log the user in
            login(request, user)
            
            messages.success(request, 'Registration successful! Welcome to Taw Haa Zin Nurain Online Madarasa.')
            return redirect('dashboard')
    else:
        user_form = UserRegistrationForm()
        student_form = StudentRegistrationForm()
    
    context = {
        'user_form': user_form,
        'student_form': student_form,
        'title': 'Register - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'auth/register.html', context)

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'core:dashboard')
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'title': 'Login - Taw Haa Zin Nurain Online Madarasa',
    }
    return render(request, 'auth/login.html', context)

def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:home')


