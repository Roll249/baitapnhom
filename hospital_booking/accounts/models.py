from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model with role-based access"""
    ROLE_CHOICES = [
        ('patient', 'Bệnh nhân'),
        ('doctor', 'Bác sĩ'),
        ('admin', 'Quản trị viên'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def is_patient(self):
        return self.role == 'patient'
    
    def is_doctor(self):
        return self.role == 'doctor'
    
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
