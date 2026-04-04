from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncMonth
from datetime import date
from .models import Appointment, Billing
from doctors.models import Doctor, Specialization
from patients.models import Patient
from accounts.models import User


def admin_required(view_func):
    """Decorator to ensure user is an admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_user():
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard view"""
    # Statistics
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    
    # Recent appointments
    recent_appointments = Appointment.objects.all().order_by('-created_at')[:10]
    
    # Appointments by status
    status_stats = Appointment.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
        'status_stats': list(status_stats),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@admin_required
def manage_patients(request):
    """Manage patients"""
    patients = Patient.objects.all().order_by('-created_at')
    
    search = request.GET.get('search', '')
    if search:
        patients = patients.filter(
            user__username__icontains=search
        ) | patients.filter(
            user__first_name__icontains=search
        ) | patients.filter(
            user__last_name__icontains=search
        )
    
    context = {
        'patients': patients,
        'search': search,
    }
    return render(request, 'admin_panel/patients.html', context)


@login_required
@admin_required
def manage_doctors(request):
    """Manage doctors"""
    doctors = Doctor.objects.all().order_by('-created_at')
    specializations = Specialization.objects.all()
    
    spec_filter = request.GET.get('specialization', '')
    if spec_filter:
        doctors = doctors.filter(specialization_id=spec_filter)
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'spec_filter': spec_filter,
    }
    return render(request, 'admin_panel/doctors.html', context)


@login_required
@admin_required
def manage_appointments(request):
    """Manage all appointments"""
    appointments = Appointment.objects.all().order_by('-appointment_date')
    
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    return render(request, 'admin_panel/appointments.html', context)


@login_required
@admin_required
def admin_reports(request):
    """Generate reports"""
    # Appointments by month
    monthly_appointments = Appointment.objects.annotate(
        month=TruncMonth('appointment_date')
    ).values('month').annotate(count=Count('id')).order_by('month')
    
    # Appointments by doctor
    doctor_appointments = Appointment.objects.values(
        'doctor__user__first_name', 'doctor__user__last_name'
    ).annotate(count=Count('id')).order_by('-count')[:10]
    
    # Appointments by specialization
    spec_appointments = Appointment.objects.values(
        'doctor__specialization__name'
    ).annotate(count=Count('id')).order_by('-count')
    
    context = {
        'monthly_appointments': list(monthly_appointments),
        'doctor_appointments': list(doctor_appointments),
        'spec_appointments': list(spec_appointments),
    }
    return render(request, 'admin_panel/reports.html', context)


@login_required
@admin_required
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    status = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
    messages.success(request, f'Đã {status} tài khoản {user.username}.')
    
    if user.is_patient():
        return redirect('manage_patients')
    else:
        return redirect('manage_doctors')
