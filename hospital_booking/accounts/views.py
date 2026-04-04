from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import PatientRegistrationForm, UserLoginForm, UserProfileForm, PatientProfileForm
from patients.models import Patient


def home(request):
    """Home page view"""
    return render(request, 'home.html')


def register(request):
    """Patient registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'patient'
            user.save()
            
            # Create patient profile
            Patient.objects.create(
                user=user,
                date_of_birth=form.cleaned_data.get('date_of_birth'),
                gender=form.cleaned_data.get('gender', '')
            )
            
            login(request, user)
            messages.success(request, 'Đăng ký thành công! Chào mừng bạn đến với hệ thống.')
            return redirect('dashboard')
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Xin chào {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất.')
    return redirect('home')


@login_required
def dashboard(request):
    """Dashboard view based on user role"""
    user = request.user
    
    if user.is_admin_user():
        return redirect('admin_dashboard')
    elif user.is_doctor():
        return redirect('doctor_dashboard')
    else:
        return redirect('patient_dashboard')


@login_required
def profile(request):
    """User profile view"""
    user = request.user
    patient_form = None
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        
        if user.is_patient() and hasattr(user, 'patient_profile'):
            patient_form = PatientProfileForm(request.POST, instance=user.patient_profile)
            if user_form.is_valid() and patient_form.is_valid():
                user_form.save()
                patient_form.save()
                messages.success(request, 'Cập nhật thông tin thành công!')
                return redirect('profile')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Cập nhật thông tin thành công!')
                return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        if user.is_patient() and hasattr(user, 'patient_profile'):
            patient_form = PatientProfileForm(instance=user.patient_profile)
    
    context = {
        'user_form': user_form,
        'patient_form': patient_form,
    }
    return render(request, 'accounts/profile.html', context)
