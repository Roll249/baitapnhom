from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('patients/', views.manage_patients, name='manage_patients'),
    path('doctors/', views.manage_doctors, name='manage_doctors'),
    path('appointments/', views.manage_appointments, name='manage_appointments'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('user/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
]
