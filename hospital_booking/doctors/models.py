from django.db import models
from accounts.models import User


class Specialization(models.Model):
    """Medical specialization categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Chuyên khoa'
        verbose_name_plural = 'Chuyên khoa'


class Doctor(models.Model):
    """Doctor profile linked to user account"""
    STATUS_CHOICES = [
        ('available', 'Đang làm việc'),
        ('busy', 'Bận'),
        ('off', 'Nghỉ phép'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, related_name='doctors')
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"BS. {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        verbose_name = 'Bác sĩ'
        verbose_name_plural = 'Bác sĩ'


class DoctorSchedule(models.Model):
    """Doctor's working schedule"""
    WEEKDAY_CHOICES = [
        (0, 'Thứ Hai'),
        (1, 'Thứ Ba'),
        (2, 'Thứ Tư'),
        (3, 'Thứ Năm'),
        (4, 'Thứ Sáu'),
        (5, 'Thứ Bảy'),
        (6, 'Chủ Nhật'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_patients = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()} ({self.start_time} - {self.end_time})"
    
    class Meta:
        verbose_name = 'Lịch làm việc'
        verbose_name_plural = 'Lịch làm việc'
        unique_together = ['doctor', 'weekday', 'start_time']
