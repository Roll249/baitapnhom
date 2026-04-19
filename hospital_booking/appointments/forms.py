from django import forms
from django.forms import HiddenInput
from .models import Appointment
from doctors.models import Doctor


class AppointmentForm(forms.ModelForm):
    """Form for creating appointments"""
    
    # Additional patient info fields
    patient_name = forms.CharField(
        max_length=100,
        label='Họ và tên',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập họ tên đầy đủ'
        })
    )
    patient_phone = forms.CharField(
        max_length=15,
        label='Số điện thoại',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0901234567'
        })
    )
    patient_email = forms.EmailField(
        label='Email',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    patient_dob = forms.DateField(
        label='Ngày sinh',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    patient_gender = forms.ChoiceField(
        label='Giới tính',
        choices=[('', '-- Chọn --'), ('M', 'Nam'), ('F', 'Nữ'), ('O', 'Khác')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'symptoms']
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_doctor'
            }),
            'appointment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_appointment_date'
            }),
            'appointment_time': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_appointment_time'
            }),
            'symptoms': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Mô tả triệu chứng của bạn (VD: Đau đầu, sốt nhẹ 2 ngày)...'
            }),
        }
        labels = {
            'doctor': 'Chọn bác sĩ *',
            'appointment_date': 'Ngày khám *',
            'appointment_time': 'Giờ khám *',
            'symptoms': 'Triệu chứng',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make doctor field optional in display but required in model
        self.fields['doctor'].empty_label = '-- Chọn bác sĩ --'
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')
        
        if doctor and appointment_date and appointment_time:
            # Check if this slot is available
            day_of_week = appointment_date.weekday()
            schedule = doctor.schedules.filter(weekday=day_of_week, is_active=True).first()
            
            if not schedule:
                raise forms.ValidationError(
                    f'Bác sĩ {doctor} không làm việc vào ngày này. '
                    f'Vui lòng chọn ngày trong tuần (Thứ 2 - Thứ 6).'
                )
            
            # Check if slot is already booked
            from .models import Appointment
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing:
                raise forms.ValidationError(
                    'Khung giờ này đã có người đặt. Vui lòng chọn giờ khác.'
                )
        
        return cleaned_data


class AppointmentStatusForm(forms.ModelForm):
    """Form for doctor to update appointment status"""
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ghi chú...'}),
        }
        labels = {
            'status': 'Trạng thái',
            'notes': 'Ghi chú',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
