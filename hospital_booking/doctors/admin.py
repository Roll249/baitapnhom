from django.contrib import admin
from .models import Doctor, Specialization, DoctorSchedule


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'experience_years', 'consultation_fee', 'status']
    list_filter = ['specialization', 'status', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'weekday', 'start_time', 'end_time', 'max_patients', 'is_active']
    list_filter = ['weekday', 'is_active']
    search_fields = ['doctor__user__username']
