from django.db import models
from patients.models import Patient
from doctors.models import Doctor


class Appointment(models.Model):
    """Appointment between patient and doctor"""
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
        ('rejected', 'Từ chối'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    symptoms = models.TextField(blank=True, help_text='Mô tả triệu chứng')
    notes = models.TextField(blank=True, help_text='Ghi chú của bác sĩ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} - {self.doctor} ({self.appointment_date})"
    
    class Meta:
        verbose_name = 'Lịch khám'
        verbose_name_plural = 'Lịch khám'
        ordering = ['-appointment_date', '-appointment_time']


class Billing(models.Model):
    """Billing for completed appointments"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Chưa thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('refunded', 'Đã hoàn tiền'),
    ]
    
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='billing')
    amount = models.DecimalField(max_digits=10, decimal_places=0)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Hóa đơn #{self.id} - {self.appointment}"
    
    class Meta:
        verbose_name = 'Hóa đơn'
        verbose_name_plural = 'Hóa đơn'
