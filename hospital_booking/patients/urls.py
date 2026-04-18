from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment_doctor'),
    path('appointments/', views.my_appointments, name='my_appointments'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('appointments/<int:appointment_id>/rate/', views.rate_doctor, name='rate_doctor'),
    path('appointments/<int:appointment_id>/medical-record/', views.view_patient_medical_record, name='view_medical_record'),
    path('confirmation/<int:confirmation_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('waiting-list/add/', views.add_to_waiting_list, name='add_to_waiting_list'),
]
