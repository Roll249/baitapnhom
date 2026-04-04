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
]
