from django.db import models
from accounts.models import User


class Notification(models.Model):
    """In-app notification model"""
    NOTIFICATION_TYPES = [
        ('appointment_new', 'Lịch hẹn mới'),
        ('appointment_confirmed', 'Lịch hẹn được xác nhận'),
        ('appointment_cancelled', 'Lịch hẹn bị hủy'),
        ('appointment_completed', 'Lịch hẹn hoàn thành'),
        ('appointment_reminder', 'Nhắc lịch hẹn'),
        ('payment_success', 'Thanh toán thành công'),
        ('system', 'Thông báo hệ thống'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class EmailLog(models.Model):
    """Log sent emails for tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    subject = models.CharField(max_length=255)
    recipient = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='sent')
    
    class Meta:
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
        ordering = ['-sent_at']
