from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Notification, EmailLog


def create_notification(user, notification_type, title, message, link=''):
    """Create an in-app notification"""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )


def send_email_notification(user, subject, template_name, context):
    """Send email notification to user"""
    if not user.email:
        return False
    
    try:
        html_message = render_to_string(template_name, context)
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        EmailLog.objects.create(
            user=user,
            subject=subject,
            recipient=user.email,
            status='sent'
        )
        return True
    except Exception as e:
        EmailLog.objects.create(
            user=user,
            subject=subject,
            recipient=user.email,
            status=f'failed: {str(e)}'
        )
        return False


def notify_appointment_created(appointment):
    """Notify doctor when new appointment is created"""
    doctor_user = appointment.doctor.user
    patient_name = str(appointment.patient)
    
    create_notification(
        user=doctor_user,
        notification_type='appointment_new',
        title='Lịch hẹn mới',
        message=f'Bệnh nhân {patient_name} đã đặt lịch khám vào ngày {appointment.appointment_date}',
        link=f'/doctor/appointments/'
    )
    
    send_email_notification(
        doctor_user,
        'Có lịch hẹn mới',
        'notifications/email/appointment_new.html',
        {'appointment': appointment}
    )


def notify_appointment_confirmed(appointment):
    """Notify patient when appointment is confirmed"""
    patient_user = appointment.patient.user
    doctor_name = str(appointment.doctor)
    
    create_notification(
        user=patient_user,
        notification_type='appointment_confirmed',
        title='Lịch hẹn được xác nhận',
        message=f'{doctor_name} đã xác nhận lịch hẹn ngày {appointment.appointment_date} lúc {appointment.appointment_time}',
        link='/patient/appointments/'
    )
    
    send_email_notification(
        patient_user,
        'Lịch hẹn của bạn đã được xác nhận',
        'notifications/email/appointment_confirmed.html',
        {'appointment': appointment}
    )


def notify_appointment_cancelled(appointment, cancelled_by='patient'):
    """Notify relevant party when appointment is cancelled"""
    if cancelled_by == 'patient':
        notify_user = appointment.doctor.user
        message = f'Bệnh nhân {appointment.patient} đã hủy lịch hẹn ngày {appointment.appointment_date}'
    else:
        notify_user = appointment.patient.user
        message = f'Bác sĩ {appointment.doctor} đã hủy lịch hẹn ngày {appointment.appointment_date}'
    
    create_notification(
        user=notify_user,
        notification_type='appointment_cancelled',
        title='Lịch hẹn đã bị hủy',
        message=message,
        link='/appointments/'
    )


def notify_payment_success(billing):
    """Notify patient when payment is successful"""
    patient_user = billing.appointment.patient.user
    
    create_notification(
        user=patient_user,
        notification_type='payment_success',
        title='Thanh toán thành công',
        message=f'Đã thanh toán thành công {billing.amount:,.0f} VNĐ cho lịch khám ngày {billing.appointment.appointment_date}',
        link='/patient/appointments/'
    )
    
    send_email_notification(
        patient_user,
        'Thanh toán thành công',
        'notifications/email/payment_success.html',
        {'billing': billing}
    )
