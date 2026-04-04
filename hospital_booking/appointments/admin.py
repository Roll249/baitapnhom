from django.contrib import admin
from .models import Appointment, Billing


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'appointment_date', 'doctor']
    search_fields = ['patient__user__username', 'doctor__user__username']
    ordering = ['-appointment_date', '-appointment_time']
    date_hierarchy = 'appointment_date'


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'amount', 'payment_status', 'payment_date']
    list_filter = ['payment_status', 'created_at']
    search_fields = ['appointment__patient__user__username']
