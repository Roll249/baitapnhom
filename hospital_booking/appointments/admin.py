from django.contrib import admin
from .models import Appointment, Billing, BookingConfirmation, WaitingList, MedicalRecord, Prescription


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'checked_in', 'created_at']
    list_filter = ['status', 'appointment_date', 'doctor', 'checked_in']
    search_fields = ['patient__user__username', 'doctor__user__username']
    ordering = ['-appointment_date', '-appointment_time']
    date_hierarchy = 'appointment_date'
    readonly_fields = ['checked_in', 'checked_in_at']


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'amount', 'payment_status', 'payment_date', 'payment_method']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['appointment__patient__user__username', 'transaction_id']


@admin.register(BookingConfirmation)
class BookingConfirmationAdmin(admin.ModelAdmin):
    list_display = ['confirmation_code', 'appointment', 'created_at']
    search_fields = ['confirmation_code', 'appointment__patient__user__username']
    readonly_fields = ['confirmation_code', 'qr_data', 'created_at']


@admin.register(WaitingList)
class WaitingListAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'preferred_date', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['patient__user__username', 'doctor__user__username']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'created_at', 'updated_at']
    search_fields = ['appointment__patient__user__username', 'diagnosis']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['medical_record', 'medicine_name', 'dosage', 'frequency', 'created_at']
    search_fields = ['medicine_name', 'medical_record__appointment__patient__user__username']
