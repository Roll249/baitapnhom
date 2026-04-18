from django.contrib import admin
from .models import Doctor, Specialization, DoctorSchedule, DoctorRating


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'experience_years', 'consultation_fee', 'status', 'clinic_name']
    list_filter = ['specialization', 'status', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'clinic_name']
    ordering = ['-created_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'specialization', 'status')
        }),
        ('Thông tin chuyên môn', {
            'fields': ('qualification', 'experience_years', 'bio')
        }),
        ('Phí khám', {
            'fields': ('consultation_fee',)
        }),
        ('Thông tin phòng khám', {
            'fields': ('clinic_name', 'clinic_address', 'clinic_phone', 'clinic_map_url'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'weekday', 'start_time', 'end_time', 'max_patients', 'buffer_minutes', 'is_active']
    list_filter = ['weekday', 'is_active']
    search_fields = ['doctor__user__username']


@admin.register(DoctorRating)
class DoctorRatingAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'rating', 'patient_name', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['doctor__user__username', 'patient_name']
    ordering = ['-created_at']
