from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'gender', 'date_of_birth', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']
