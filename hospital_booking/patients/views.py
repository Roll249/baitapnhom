from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from doctors.models import Doctor, Specialization
from appointments.models import Appointment, BookingConfirmation, WaitingList
from appointments.forms import AppointmentForm
from notifications.services import notify_appointment_created, notify_appointment_cancelled


def patient_required(view_func):
    """Decorator to ensure user is a patient"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_patient():
            messages.error(request, 'Bạn không có quyền truy cập trang này.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@patient_required
def patient_dashboard(request):
    """Patient dashboard view"""
    patient = request.user.patient_profile
    
    # Get recent appointments
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')[:5]
    pending_count = Appointment.objects.filter(patient=patient, status='pending').count()
    confirmed_count = Appointment.objects.filter(patient=patient, status='confirmed').count()
    
    context = {
        'appointments': appointments,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
    }
    return render(request, 'patients/dashboard.html', context)


@login_required
@patient_required
def doctor_list(request):
    """List all available doctors with advanced search"""
    specializations = Specialization.objects.all()
    doctors = Doctor.objects.filter(status='available')
    
    # Search by name
    query = request.GET.get('q', '').strip()
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(specialization__name__icontains=query) |
            Q(bio__icontains=query)
        )
    
    # Filter by specialization
    spec_id = request.GET.get('specialization')
    if spec_id:
        doctors = doctors.filter(specialization_id=spec_id)
    
    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        doctors = doctors.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'experience':
        doctors = doctors.order_by('-experience_years')
    elif sort_by == 'fee_low':
        doctors = doctors.order_by('consultation_fee')
    elif sort_by == 'fee_high':
        doctors = doctors.order_by('-consultation_fee')
    elif sort_by == 'rating':
        pass  # Already using default ordering
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'selected_spec': spec_id,
        'sort_by': sort_by,
    }
    return render(request, 'patients/doctor_list.html', context)


@login_required
@patient_required
def doctor_detail(request, doctor_id):
    """View doctor details"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    schedules = doctor.schedules.filter(is_active=True)
    
    context = {
        'doctor': doctor,
        'schedules': schedules,
    }
    return render(request, 'patients/doctor_detail.html', context)


@login_required
@patient_required
def book_appointment(request, doctor_id=None):
    """Book an appointment"""
    from django.utils import timezone
    
    patient = request.user.patient_profile
    initial = {}
    
    if doctor_id:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        initial['doctor'] = doctor
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.status = 'pending'
            appointment.save()
            
            # Create booking confirmation with QR code
            confirmation = BookingConfirmation.objects.create(appointment=appointment)
            
            # Send notification to doctor
            notify_appointment_created(appointment)
            
            messages.success(request, f'Đặt lịch khám thành công! Mã xác nhận: {confirmation.confirmation_code}')
            return redirect('booking_confirmation', confirmation_id=confirmation.id)
    else:
        form = AppointmentForm(initial=initial)
    
    # Get all available doctors with their schedules
    doctors = Doctor.objects.filter(status='available').prefetch_related('schedules', 'specialization')
    specializations = Specialization.objects.all()
    
    context = {
        'form': form,
        'doctor_id': doctor_id,
        'doctors': doctors,
        'specializations': specializations,
        'today': timezone.now().date(),
    }
    return render(request, 'patients/book_appointment.html', context)


@login_required
@patient_required
def booking_confirmation(request, confirmation_id):
    """View booking confirmation with QR code"""
    confirmation = get_object_or_404(BookingConfirmation, id=confirmation_id)
    
    # Check if user owns this appointment
    if confirmation.appointment.patient.user != request.user:
        messages.error(request, 'Bạn không có quyền xem phiếu khám này.')
        return redirect('my_appointments')
    
    context = {
        'confirmation': confirmation,
    }
    return render(request, 'patients/booking_confirmation.html', context)


@login_required
@patient_required
def my_appointments(request):
    """View patient's appointments"""
    patient = request.user.patient_profile
    status_filter = request.GET.get('status', '')
    
    appointments = Appointment.objects.filter(patient=patient)
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    context = {
        'appointments': appointments,
        'status_filter': status_filter,
    }
    return render(request, 'patients/my_appointments.html', context)


@login_required
@patient_required
def cancel_appointment(request, appointment_id):
    """Cancel an appointment"""
    patient = request.user.patient_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)
    
    if appointment.status in ['pending', 'confirmed']:
        appointment.status = 'cancelled'
        appointment.save()
        
        # Notify doctor about cancellation
        notify_appointment_cancelled(appointment, 'patient')
        
        messages.success(request, 'Đã hủy lịch khám thành công.')
    else:
        messages.error(request, 'Không thể hủy lịch khám này.')
    
    return redirect('my_appointments')


@login_required
@patient_required
def reschedule_appointment(request, appointment_id):
    """Reschedule an appointment"""
    patient = request.user.patient_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)
    
    # Check if appointment can be rescheduled
    if appointment.status not in ['pending', 'confirmed']:
        messages.error(request, 'Chỉ có thể đổi lịch khi lịch đang chờ xác nhận hoặc đã xác nhận.')
        return redirect('my_appointments')
    
    # Check if it's at least 2 hours before appointment
    appointment_datetime = timezone.make_aware(
        datetime.combine(appointment.appointment_date, appointment.appointment_time)
    )
    if timezone.now() + timedelta(hours=2) > appointment_datetime:
        messages.error(request, 'Chỉ có thể đổi lịch trước giờ hẹn ít nhất 2 tiếng.')
        return redirect('my_appointments')
    
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        reason = request.POST.get('reason', '')
        
        if new_date and new_time:
            try:
                appointment.appointment_date = new_date
                appointment.appointment_time = new_time
                appointment.save()
                
                # Update confirmation if exists
                if hasattr(appointment, 'confirmation'):
                    appointment.confirmation.save()
                
                messages.success(request, 'Đổi lịch khám thành công!')
                return redirect('my_appointments')
            except Exception as e:
                messages.error(request, f'Không thể đổi lịch: {str(e)}')
        else:
            messages.error(request, 'Vui lòng chọn ngày và giờ mới.')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'patients/reschedule_appointment.html', context)


@login_required
@patient_required
def add_to_waiting_list(request):
    """Add patient to waiting list for a doctor"""
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        preferred_date = request.POST.get('preferred_date')
        preferred_slots = request.POST.getlist('preferred_slots')
        notes = request.POST.get('notes', '')
        
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            patient = request.user.patient_profile
            
            WaitingList.objects.create(
                patient=patient,
                doctor=doctor,
                preferred_date=preferred_date,
                preferred_time_slots=preferred_slots,
                notes=notes
            )
            
            messages.success(request, 'Đã thêm vào danh sách chờ. Chúng tôi sẽ thông báo khi có lịch trống.')
        except Doctor.DoesNotExist:
            messages.error(request, 'Không tìm thấy bác sĩ.')
    
    return redirect('doctor_list')


@login_required
@patient_required
def rate_doctor(request, appointment_id):
    """Rate a doctor after completed appointment"""
    from doctors.models import DoctorRating
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user owns this appointment
    if appointment.patient.user != request.user:
        messages.error(request, 'Bạn không có quyền đánh giá lịch khám này.')
        return redirect('my_appointments')
    
    # Check if appointment is completed
    if appointment.status != 'completed':
        messages.error(request, 'Chỉ có thể đánh giá sau khi đã khám xong.')
        return redirect('my_appointments')
    
    # Check if already rated
    if hasattr(appointment, 'rating'):
        messages.error(request, 'Bạn đã đánh giá lịch khám này.')
        return redirect('my_appointments')
    
    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')
        
        if rating < 1 or rating > 5:
            messages.error(request, 'Vui lòng chọn điểm đánh giá từ 1-5 sao.')
            return redirect('rate_doctor', appointment_id=appointment_id)
        
        DoctorRating.objects.create(
            doctor=appointment.doctor,
            appointment=appointment,
            patient_name=str(appointment.patient),
            rating=rating,
            comment=comment
        )
        
        messages.success(request, 'Cảm ơn bạn đã đánh giá!')
        return redirect('my_appointments')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'patients/rate_doctor.html', context)


@login_required
@patient_required
def view_patient_medical_record(request, appointment_id):
    """View medical record for patient"""
    from appointments.models import MedicalRecord
    
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check if user owns this appointment
    if appointment.patient.user != request.user:
        messages.error(request, 'Bạn không có quyền xem hồ sơ khám này.')
        return redirect('my_appointments')
    
    # Check if medical record exists
    if not hasattr(appointment, 'medical_record'):
        messages.error(request, 'Chưa có hồ sơ khám bệnh cho lịch hẹn này.')
        return redirect('my_appointments')
    
    context = {
        'appointment': appointment,
        'medical_record': appointment.medical_record,
    }
    return render(request, 'patients/view_medical_record.html', context)
