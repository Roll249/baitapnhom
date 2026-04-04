from django import forms
from .models import Doctor, DoctorSchedule, Specialization


class DoctorProfileForm(forms.ModelForm):
    """Form for updating doctor profile"""
    class Meta:
        model = Doctor
        fields = ['specialization', 'qualification', 'experience_years', 'consultation_fee', 'status', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class DoctorScheduleForm(forms.ModelForm):
    """Form for managing doctor schedule"""
    class Meta:
        model = DoctorSchedule
        fields = ['weekday', 'start_time', 'end_time', 'max_patients', 'is_active']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'is_active':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-check-input'
