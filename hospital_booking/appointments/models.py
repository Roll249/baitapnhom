from django.db import models
from django.core.exceptions import ValidationError
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

    def clean(self):
        """Validate appointment data"""
        if not self.doctor:
            return
            
        if self.doctor.status == 'off':
            raise ValidationError('Bác sĩ đang nghỉ phép, không thể đặt lịch.')

        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            raise ValidationError('Bác sĩ đã có lịch khám vào thời gian này.')

        day_of_week = self.appointment_date.weekday()
        schedule = self.doctor.schedules.filter(weekday=day_of_week, is_active=True).first()
        
        if not schedule:
            raise ValidationError('Bác sĩ không làm việc vào ngày này.')
        
        active_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            status__in=['pending', 'confirmed']
        ).exclude(pk=self.pk).count()
        
        if schedule.max_patients and active_appointments >= schedule.max_patients:
            raise ValidationError(
                f'Bác sĩ đã đạt số lượng bệnh nhân tối đa ({schedule.max_patients}) trong ngày này.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
    consultation_fee_snapshot = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        blank=True,
        null=True,
        help_text='Phí khám tại thời điểm tạo hóa đơn (snapshot để tránh thay đổi)'
    )
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Mã giao dịch từ cổng thanh toán'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hóa đơn #{self.id} - {self.appointment}"

    def save(self, *args, **kwargs):
        if not self.consultation_fee_snapshot and self.appointment:
            self.consultation_fee_snapshot = self.appointment.doctor.consultation_fee
        if not self.amount and self.appointment:
            self.amount = self.consultation_fee_snapshot or self.appointment.doctor.consultation_fee
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Hóa đơn'
        verbose_name_plural = 'Hóa đơn'
