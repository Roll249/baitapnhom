from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('appointments/<int:appointment_id>/update/', views.update_appointment, name='update_appointment'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
    path('schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('schedule/<int:schedule_id>/delete/', views.delete_schedule, name='delete_schedule'),
    path('statistics/', views.doctor_statistics, name='doctor_statistics'),
]
