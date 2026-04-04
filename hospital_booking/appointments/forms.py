from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    """Form for creating appointments"""
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'appointment_time', 'symptoms']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'type': 'time'}),
            'symptoms': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Mô tả triệu chứng của bạn...'}),
        }
        labels = {
            'doctor': 'Chọn bác sĩ',
            'appointment_date': 'Ngày khám',
            'appointment_time': 'Giờ khám',
            'symptoms': 'Triệu chứng',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


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
