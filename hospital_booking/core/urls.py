"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from accounts.views import home, dashboard

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('patient/', include('patients.urls')),
    path('doctor/', include('doctors.urls')),
    path('management/', include('appointments.urls')),
    path('notifications/', include('notifications.urls')),
    path('payment/', include('payments.urls')),
    path('api/', include('api.urls')),
]
