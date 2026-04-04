from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from patients.models import Patient


class PatientRegistrationForm(UserCreationForm):
    """Form for patient registration"""
    first_name = forms.CharField(max_length=30, required=True, label='Họ')
    last_name = forms.CharField(max_length=30, required=True, label='Tên')
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=15, required=True, label='Số điện thoại')
    date_of_birth = forms.DateField(
        required=False, 
        label='Ngày sinh',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=[('', '-- Chọn --')] + list(Patient.GENDER_CHOICES),
        required=False,
        label='Giới tính'
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserLoginForm(forms.Form):
    """Login form"""
    username = forms.CharField(label='Tên đăng nhập')
    password = forms.CharField(widget=forms.PasswordInput, label='Mật khẩu')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class PatientProfileForm(forms.ModelForm):
    """Form for updating patient profile"""
    class Meta:
        model = Patient
        fields = ['date_of_birth', 'gender', 'insurance_info', 'medical_history']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_history': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
