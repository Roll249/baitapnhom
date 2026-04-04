from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Doctor, Specialization
from appointments.models import Appointment
from appointments.forms import AppointmentForm


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
    """List all available doctors"""
    specializations = Specialization.objects.all()
    doctors = Doctor.objects.filter(status='available')
    
    # Filter by specialization
    spec_id = request.GET.get('specialization')
    if spec_id:
        doctors = doctors.filter(specialization_id=spec_id)
    
    context = {
        'doctors': doctors,
        'specializations': specializations,
        'selected_spec': spec_id,
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
            messages.success(request, 'Đặt lịch khám thành công! Vui lòng chờ bác sĩ xác nhận.')
            return redirect('my_appointments')
    else:
        form = AppointmentForm(initial=initial)
    
    context = {
        'form': form,
        'doctor_id': doctor_id,
    }
    return render(request, 'patients/book_appointment.html', context)


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
        messages.success(request, 'Đã hủy lịch khám thành công.')
    else:
        messages.error(request, 'Không thể hủy lịch khám này.')
    
    return redirect('my_appointments')
