from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointments/<int:appointment_id>/update/', views.update_appointment, name='update_appointment'),
    path('appointments/<int:appointment_id>/medical-record/', views.add_medical_record, name='add_medical_record'),
    path('appointments/<int:appointment_id>/checkin/', views.check_in_appointment, name='check_in'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
    path('schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('schedule/<int:schedule_id>/delete/', views.delete_schedule, name='delete_schedule'),
    path('statistics/', views.doctor_statistics, name='doctor_statistics'),
    path('medical-records/<int:record_id>/', views.view_medical_record_doctor, name='view_medical_record_doctor'),
    path('medical-records/<int:record_id>/prescription/', views.add_prescription, name='add_prescription'),
]
