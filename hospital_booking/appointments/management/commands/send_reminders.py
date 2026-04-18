"""
Management command to send appointment reminders
Run: python manage.py send_reminders
Schedule with crontab: 0 * * * * python /path/to/manage.py send_reminders
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment
from notifications.services import send_email_notification
from django.conf import settings


class Command(BaseCommand):
    help = 'Send appointment reminders to patients'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Reminder 1: 24 hours before
        tomorrow = (now + timedelta(hours=24)).date()
        appointments_24h = Appointment.objects.filter(
            appointment_date=tomorrow,
            status='confirmed'
        ).select_related('patient__user', 'doctor')

        for apt in appointments_24h:
            # Check if reminder was already sent (within last 24h)
            if not self._reminder_sent(apt, '24h'):
                self._send_reminder(apt, '24h', tomorrow)
                self.stdout.write(
                    self.style.SUCCESS(f'Sent 24h reminder for appointment #{apt.id}')
                )

        # Reminder 2: 2 hours before
        two_hours_later = now + timedelta(hours=2)
        appointments_2h = Appointment.objects.filter(
            appointment_date=two_hours_later.date(),
            appointment_time__hour=two_hours_later.hour,
            status='confirmed'
        ).select_related('patient__user', 'doctor')

        for apt in appointments_2h:
            if not self._reminder_sent(apt, '2h'):
                self._send_reminder(apt, '2h', tomorrow)
                self.stdout.write(
                    self.style.SUCCESS(f'Sent 2h reminder for appointment #{apt.id}')
                )

        self.stdout.write(self.style.SUCCESS('Reminder process completed'))

    def _reminder_sent(self, appointment, reminder_type):
        """Check if reminder was already sent"""
        # Simple check: look for recent notifications
        from notifications.models import Notification
        recent = timezone.now() - timedelta(hours=24)
        
        if reminder_type == '24h':
            return Notification.objects.filter(
                user=appointment.patient.user,
                notification_type='reminder_24h',
                created_at__gte=recent
            ).exists()
        else:
            return Notification.objects.filter(
                user=appointment.patient.user,
                notification_type='reminder_2h',
                created_at__gte=recent
            ).exists()

    def _send_reminder(self, appointment, reminder_type, reminder_date):
        """Send reminder notification and email"""
        from notifications.models import Notification
        
        patient = appointment.patient
        doctor = appointment.doctor

        if reminder_type == '24h':
            notification_type = 'reminder_24h'
            title = 'Nhắc lịch khám ngày mai'
            message = (
                f'Bạn có lịch khám với BS. {doctor} vào ngày mai '
                f'{appointment.appointment_date} lúc {appointment.appointment_time}. '
                f'Vui lòng đến trước 15 phút.'
            )
        else:
            notification_type = 'reminder_2h'
            title = 'Nhắc lịch khám sắp tới'
            message = (
                f'Bạn có lịch khám với BS. {doctor} sau 2 giờ nữa '
                f'lúc {appointment.appointment_time}. Vui lòng đến đúng giờ.'
            )

        # Create in-app notification
        Notification.objects.create(
            user=patient.user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=f'/patient/appointments/'
        )

        # Send email if configured
        if patient.user.email and settings.EMAIL_HOST_USER:
            self.stdout.write(f'Would send email to {patient.user.email}')
            # Uncomment to actually send email:
            # send_email_notification(
            #     patient.user,
            #     title,
            #     'notifications/email/reminder.html',
            #     {'appointment': appointment, 'reminder_type': reminder_type}
            # )
