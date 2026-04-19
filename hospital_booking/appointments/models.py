from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from patients.models import Patient
from doctors.models import Doctor
import uuid
import json


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
    checked_in = models.BooleanField(default=False, help_text='Đã check-in khi đến khám')
    checked_in_at = models.DateTimeField(null=True, blank=True)
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
            status__in=['pending', 'confirmed'],
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
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=Q(status__in=['pending', 'confirmed']),
                name='uniq_active_appointment_slot',
            )
        ]


class BookingConfirmation(models.Model):
    """Electronic booking ticket with QR code"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='confirmation')
    confirmation_code = models.CharField(max_length=20, unique=True, help_text='Mã xác nhận')
    qr_data = models.TextField(blank=True, help_text='Dữ liệu cho QR code (JSON)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Mã xác nhận: {self.confirmation_code}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = f"BK{uuid.uuid4().hex[:8].upper()}"
        if not self.qr_data:
            self.generate_qr_data()
        super().save(*args, **kwargs)
    
    def generate_qr_data(self):
        """Generate QR code data as JSON"""
        data = {
            'code': self.confirmation_code,
            'patient': str(self.appointment.patient),
            'doctor': str(self.appointment.doctor),
            'specialization': self.appointment.doctor.specialization.name if self.appointment.doctor.specialization else '',
            'date': str(self.appointment.appointment_date),
            'time': str(self.appointment.appointment_time),
            'clinic': self.appointment.doctor.clinic_name,
            'clinic_address': self.appointment.doctor.clinic_address,
        }
        self.qr_data = json.dumps(data, ensure_ascii=False)
    
    class Meta:
        verbose_name = 'Phiếu khám'
        verbose_name_plural = 'Phiếu khám'


class WaitingList(models.Model):
    """Waiting list for when appointments are full"""
    STATUS_CHOICES = [
        ('waiting', 'Đang chờ'),
        ('notified', 'Đã thông báo'),
        ('booked', 'Đã đặt'),
        ('expired', 'Hết hạn'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='waiting_list')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='waiting_list')
    preferred_date = models.DateField(help_text='Ngày mong muốn')
    preferred_time_slots = models.JSONField(
        default=list, 
        blank=True,
        help_text='Danh sách khung giờ mong muốn, ví dụ: ["08:00", "09:00"]'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text='Ghi chú của bệnh nhân')
    
    def __str__(self):
        return f"{self.patient} - {self.doctor} ({self.preferred_date})"
    
    class Meta:
        verbose_name = 'Danh sách chờ'
        verbose_name_plural = 'Danh sách chờ'
        ordering = ['-created_at']


class MedicalRecord(models.Model):
    """Medical record for completed appointments"""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    diagnosis = models.TextField(help_text='Chẩn đoán')
    notes = models.TextField(blank=True, help_text='Ghi chú chuyên môn')
    treatment_plan = models.TextField(blank=True, help_text='Kế hoạch điều trị')
    follow_up_date = models.DateField(null=True, blank=True, help_text='Ngày tái khám')
    follow_up_reason = models.TextField(blank=True, help_text='Lý do tái khám')
    attachments = models.FileField(
        upload_to='medical_records/', 
        blank=True,
        help_text='File đính kèm (kết quả xét nghiệm, ảnh...)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Hồ sơ khám: {self.appointment}"
    
    class Meta:
        verbose_name = 'Hồ sơ khám bệnh'
        verbose_name_plural = 'Hồ sơ khám bệnh'
        ordering = ['-created_at']


class Prescription(models.Model):
    """Prescription for medications"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medicine_name = models.CharField(max_length=200, help_text='Tên thuốc')
    dosage = models.CharField(max_length=100, help_text='Liều lượng (VD: 1 viên/lần)')
    frequency = models.CharField(max_length=100, help_text='Tần suất (VD: 3 lần/ngày)')
    duration = models.CharField(max_length=100, help_text='Thời gian (VD: 7 ngày)')
    instructions = models.TextField(blank=True, help_text='Hướng dẫn sử dụng')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.medicine_name} - {self.medical_record}"
    
    class Meta:
        verbose_name = 'Đơn thuốc'
        verbose_name_plural = 'Đơn thuốc'
        ordering = ['created_at']


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
