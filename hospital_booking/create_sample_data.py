"""
Script to create sample data for the Hospital Booking System
Run: python manage.py shell < create_sample_data.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from doctors.models import Doctor, Specialization, DoctorSchedule
from patients.models import Patient
from datetime import time

# Create specializations
specializations_data = [
    ('Nội tổng quát', 'Khám và điều trị các bệnh nội khoa'),
    ('Nhi khoa', 'Khám và điều trị trẻ em'),
    ('Da liễu', 'Khám và điều trị các bệnh về da'),
    ('Tim mạch', 'Khám và điều trị các bệnh tim mạch'),
    ('Thần kinh', 'Khám và điều trị các bệnh thần kinh'),
    ('Mắt', 'Khám và điều trị các bệnh về mắt'),
    ('Tai Mũi Họng', 'Khám và điều trị các bệnh tai mũi họng'),
    ('Răng Hàm Mặt', 'Khám và điều trị các bệnh răng miệng'),
]

for name, desc in specializations_data:
    spec, created = Specialization.objects.get_or_create(name=name, defaults={'description': desc})
    if created:
        print(f'Created specialization: {name}')

# Create admin user
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@hospital.com',
        'first_name': 'Quản trị',
        'last_name': 'viên',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print('Created admin user: admin / admin123')

# Create sample doctors
doctors_data = [
    ('doctor1', 'Nguyễn Văn', 'An', 'Nội tổng quát', 10, 200000),
    ('doctor2', 'Trần Thị', 'Bình', 'Nhi khoa', 8, 250000),
    ('doctor3', 'Lê Văn', 'Cường', 'Tim mạch', 15, 300000),
    ('doctor4', 'Phạm Thị', 'Dung', 'Da liễu', 5, 180000),
]

for username, first, last, spec_name, exp, fee in doctors_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@hospital.com',
            'first_name': first,
            'last_name': last,
            'role': 'doctor',
            'phone': '0901234567',
        }
    )
    if created:
        user.set_password('doctor123')
        user.save()
        
        spec = Specialization.objects.get(name=spec_name)
        doctor = Doctor.objects.create(
            user=user,
            specialization=spec,
            experience_years=exp,
            consultation_fee=fee,
            status='available',
            bio=f'Bác sĩ {first} {last} chuyên khoa {spec_name}'
        )
        
        # Create schedules
        for weekday in [0, 1, 2, 3, 4]:  # Monday to Friday
            DoctorSchedule.objects.create(
                doctor=doctor,
                weekday=weekday,
                start_time=time(8, 0),
                end_time=time(17, 0),
                max_patients=10
            )
        
        print(f'Created doctor: {username} / doctor123')

# Create sample patient
patient_user, created = User.objects.get_or_create(
    username='patient1',
    defaults={
        'email': 'patient1@email.com',
        'first_name': 'Bệnh',
        'last_name': 'Nhân',
        'role': 'patient',
        'phone': '0909999999',
    }
)
if created:
    patient_user.set_password('patient123')
    patient_user.save()
    Patient.objects.create(
        user=patient_user,
        gender='M',
    )
    print('Created patient: patient1 / patient123')

print('\n=== Sample data created successfully! ===')
print('Admin: admin / admin123')
print('Doctors: doctor1, doctor2, doctor3, doctor4 / doctor123')
print('Patient: patient1 / patient123')
