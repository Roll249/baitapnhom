from django.db import models
from accounts.models import User


class Patient(models.Model):
    """Patient profile linked to user account"""
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
        ('O', 'Khác'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    insurance_info = models.CharField(max_length=100, blank=True)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    class Meta:
        verbose_name = 'Bệnh nhân'
        verbose_name_plural = 'Bệnh nhân'
