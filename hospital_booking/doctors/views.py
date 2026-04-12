from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import date, timedelta
from .models import Doctor, DoctorSchedule
from .forms import DoctorProfileForm, DoctorScheduleForm
from appointments.models import Appointment, Billing
from appointments.forms import AppointmentStatusForm
from notifications.services import notify_appointment_confirmed, notify_appointment_cancelled


def doctor_required(view_func):
    """Decorator to ensure user is a doctor"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_doctor():
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard view"""
    doctor = request.user.doctor_profile
    today = date.today()
    
    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=today
    ).order_by('appointment_time')
    
    # Get pending appointments
    pending_appointments = Appointment.objects.filter(
        doctor=doctor,
        status='pending'
    ).order_by('appointment_date', 'appointment_time')[:5]
    
    # Statistics
    total_patients = Appointment.objects.filter(doctor=doctor).values('patient').distinct().count()
    pending_count = Appointment.objects.filter(doctor=doctor, status='pending').count()
    completed_count = Appointment.objects.filter(doctor=doctor, status='completed').count()
    
    context = {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_patients': total_patients,
        'pending_count': pending_count,
        'completed_count': completed_count,
    }
    return render(request, 'doctors/dashboard.html', context)


@login_required
@doctor_required
def doctor_appointments(request):
    """View all doctor's appointments"""
    doctor = request.user.doctor_profile
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    appointments = Appointment.objects.filter(doctor=doctor)
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    
    context = {
        'appointments': appointments,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    return render(request, 'doctors/appointments.html', context)


@login_required
@doctor_required
def update_appointment(request, appointment_id):
    """Update appointment status"""
    doctor = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    old_status = appointment.status
    
    if request.method == 'POST':
        form = AppointmentStatusForm(request.POST, instance=appointment)
        if form.is_valid():
            updated_appointment = form.save()
            
            # Send notifications based on status change
            if updated_appointment.status == 'confirmed' and old_status != 'confirmed':
                notify_appointment_confirmed(updated_appointment)
            elif updated_appointment.status == 'rejected':
                notify_appointment_cancelled(updated_appointment, 'doctor')
            elif updated_appointment.status == 'completed' and old_status != 'completed':
                # Create billing for completed appointments
                # Amount will be auto-set from doctor.consultation_fee via Billing.save()
                billing, created = Billing.objects.get_or_create(
                    appointment=updated_appointment,
                    defaults={
                        'amount': doctor.consultation_fee,
                        'consultation_fee_snapshot': doctor.consultation_fee
                    }
                )
                if not created:
                    # Update amount if billing already exists
                    billing.amount = doctor.consultation_fee
                    billing.consultation_fee_snapshot = doctor.consultation_fee
                    billing.save()
            
            messages.success(request, 'Cập nhật trạng thái lịch khám thành công.')
            return redirect('doctor_appointments')
    else:
        form = AppointmentStatusForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'doctors/update_appointment.html', context)


@login_required
@doctor_required
def doctor_profile(request):
    """Doctor profile management"""
    doctor = request.user.doctor_profile
    
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật hồ sơ thành công.')
            return redirect('doctor_profile')
    else:
        form = DoctorProfileForm(instance=doctor)
    
    context = {
        'form': form,
        'doctor': doctor,
    }
    return render(request, 'doctors/profile.html', context)


@login_required
@doctor_required
def doctor_schedule(request):
    """Manage doctor schedule"""
    doctor = request.user.doctor_profile
    schedules = DoctorSchedule.objects.filter(doctor=doctor)
    
    if request.method == 'POST':
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()
            messages.success(request, 'Thêm lịch làm việc thành công.')
            return redirect('doctor_schedule')
    else:
        form = DoctorScheduleForm()
    
    context = {
        'form': form,
        'schedules': schedules,
    }
    return render(request, 'doctors/schedule.html', context)


@login_required
@doctor_required
def delete_schedule(request, schedule_id):
    """Delete a schedule"""
    doctor = request.user.doctor_profile
    schedule = get_object_or_404(DoctorSchedule, id=schedule_id, doctor=doctor)
    schedule.delete()
    messages.success(request, 'Xóa lịch làm việc thành công.')
    return redirect('doctor_schedule')


@login_required
@doctor_required  
def doctor_statistics(request):
    """View doctor statistics"""
    doctor = request.user.doctor_profile
    
    # Get statistics for the last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    appointments_by_date = Appointment.objects.filter(
        doctor=doctor,
        appointment_date__range=[start_date, end_date]
    ).annotate(
        date=TruncDate('appointment_date')
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    status_stats = Appointment.objects.filter(doctor=doctor).values('status').annotate(count=Count('id'))
    
    context = {
        'appointments_by_date': list(appointments_by_date),
        'status_stats': list(status_stats),
    }
    return render(request, 'doctors/statistics.html', context)
