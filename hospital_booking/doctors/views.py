from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import date, timedelta
from .models import Doctor, DoctorSchedule
from .forms import DoctorProfileForm, DoctorScheduleForm
from appointments.models import Appointment, Billing, MedicalRecord, Prescription
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
                billing, created = Billing.objects.get_or_create(
                    appointment=updated_appointment,
                    defaults={
                        'amount': doctor.consultation_fee,
                        'consultation_fee_snapshot': doctor.consultation_fee
                    }
                )
                if not created:
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
def add_medical_record(request, appointment_id):
    """Add medical record for an appointment"""
    doctor = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    # Check if medical record already exists
    if hasattr(appointment, 'medical_record'):
        messages.error(request, 'Hồ sơ khám bệnh đã tồn tại.')
        return redirect('doctor_appointments')
    
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis', '')
        notes = request.POST.get('notes', '')
        treatment_plan = request.POST.get('treatment_plan', '')
        follow_up_date = request.POST.get('follow_up_date') or None
        follow_up_reason = request.POST.get('follow_up_reason', '')
        
        if not diagnosis:
            messages.error(request, 'Vui lòng nhập chẩn đoán.')
            return redirect('add_medical_record', appointment_id=appointment_id)
        
        # Create medical record
        medical_record = MedicalRecord.objects.create(
            appointment=appointment,
            diagnosis=diagnosis,
            notes=notes,
            treatment_plan=treatment_plan,
            follow_up_date=follow_up_date,
            follow_up_reason=follow_up_reason
        )
        
        # Update appointment status to completed
        appointment.status = 'completed'
        appointment.save()
        
        # Create billing if not exists
        billing, created = Billing.objects.get_or_create(
            appointment=appointment,
            defaults={
                'amount': doctor.consultation_fee,
                'consultation_fee_snapshot': doctor.consultation_fee
            }
        )
        
        messages.success(request, 'Đã tạo hồ sơ khám bệnh thành công.')
        return redirect('view_medical_record_doctor', record_id=medical_record.id)
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'doctors/add_medical_record.html', context)


@login_required
@doctor_required
def view_medical_record_doctor(request, record_id):
    """View medical record (for doctor)"""
    doctor = request.user.doctor_profile
    medical_record = get_object_or_404(MedicalRecord, id=record_id, appointment__doctor=doctor)
    
    context = {
        'medical_record': medical_record,
        'appointment': medical_record.appointment,
    }
    return render(request, 'doctors/view_medical_record.html', context)


@login_required
@doctor_required
def add_prescription(request, record_id):
    """Add prescription to medical record"""
    doctor = request.user.doctor_profile
    medical_record = get_object_or_404(MedicalRecord, id=record_id, appointment__doctor=doctor)
    
    if request.method == 'POST':
        medicine_name = request.POST.get('medicine_name', '')
        dosage = request.POST.get('dosage', '')
        frequency = request.POST.get('frequency', '')
        duration = request.POST.get('duration', '')
        instructions = request.POST.get('instructions', '')
        
        if not medicine_name or not dosage or not frequency:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin thuốc.')
            return redirect('add_prescription', record_id=record_id)
        
        Prescription.objects.create(
            medical_record=medical_record,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            instructions=instructions
        )
        
        messages.success(request, 'Đã thêm đơn thuốc thành công.')
        return redirect('view_medical_record_doctor', record_id=record_id)
    
    context = {
        'medical_record': medical_record,
    }
    return render(request, 'doctors/add_prescription.html', context)


@login_required
@doctor_required
def check_in_appointment(request):
    """Check-in appointment by code"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, 'Vui lòng nhập mã xác nhận.')
            return redirect('check_in')
        
        # Find appointment by confirmation code
        try:
            confirmation = BookingConfirmation.objects.get(confirmation_code=code.upper())
            appointment = confirmation.appointment
            
            # Check if already checked in
            if appointment.checked_in:
                messages.warning(request, f'Bệnh nhân {appointment.patient} đã check-in trước đó.')
                return redirect('check_in')
            
            # Check if appointment is confirmed
            if appointment.status != 'confirmed':
                messages.error(request, 'Lịch khám chưa được xác nhận hoặc đã bị hủy.')
                return redirect('check_in')
            
            # Perform check-in
            from django.utils import timezone
            appointment.checked_in = True
            appointment.checked_in_at = timezone.now()
            appointment.save()
            
            messages.success(request, f'Check-in thành công! Bệnh nhân: {appointment.patient}')
            return redirect('check_in')
            
        except BookingConfirmation.DoesNotExist:
            messages.error(request, 'Không tìm thấy mã xác nhận. Vui lòng kiểm tra lại.')
    
    return render(request, 'doctors/checkin.html')


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
