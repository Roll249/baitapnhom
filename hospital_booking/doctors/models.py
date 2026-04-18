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
    
    # Clinic information
    clinic_name = models.CharField(max_length=200, blank=True, help_text='Tên phòng khám')
    clinic_address = models.TextField(blank=True, help_text='Địa chỉ phòng khám')
    clinic_phone = models.CharField(max_length=15, blank=True, help_text='Số điện thoại phòng khám')
    clinic_map_url = models.URLField(blank=True, help_text='URL Google Maps iframe')
    
    # Average rating (computed, not stored)
    @property
    def average_rating(self):
        from django.db.models import Avg
        from .models import DoctorRating
        result = DoctorRating.objects.filter(doctor=self).aggregate(avg=Avg('rating'))
        return result['avg'] or 0
    
    @property
    def total_ratings(self):
        from .models import DoctorRating
        return DoctorRating.objects.filter(doctor=self).count()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"BS. {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        verbose_name = 'Bác sĩ'
        verbose_name_plural = 'Bác sĩ'


class DoctorRating(models.Model):
    """Rating and review for doctors"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ratings')
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='rating'
    )
    patient_name = models.CharField(max_length=100, blank=True, help_text='Tên bệnh nhân (nếu đặt lịch)')
    rating = models.PositiveSmallIntegerField(
        choices=[(i, f"{i} sao") for i in range(1, 6)],
        help_text='Điểm đánh giá (1-5 sao)'
    )
    comment = models.TextField(blank=True, help_text='Nhận xét của bệnh nhân')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Đánh giá bác sĩ'
        verbose_name_plural = 'Đánh giá bác sĩ'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating {self.rating} for Dr. {self.doctor}"


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
    buffer_minutes = models.PositiveIntegerField(
        default=5,
        help_text='Thời gian nghỉ giữa các ca (phút)'
    )
    
    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()} ({self.start_time} - {self.end_time})"
    
    class Meta:
        verbose_name = 'Lịch làm việc'
        verbose_name_plural = 'Lịch làm việc'
        unique_together = ['doctor', 'weekday', 'start_time']
