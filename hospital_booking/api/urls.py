from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'specializations', views.SpecializationViewSet, basename='specialization')
router.register(r'doctors', views.DoctorViewSet, basename='doctor')
router.register(r'patient/appointments', views.PatientAppointmentViewSet, basename='patient-appointment')
router.register(r'doctor/appointments', views.DoctorAppointmentViewSet, basename='doctor-appointment')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # JWT Auth endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User endpoints
    path('register/', views.RegisterView.as_view(), name='api_register'),
    path('profile/', views.UserProfileView.as_view(), name='api_profile'),
    
    # Router URLs
    path('', include(router.urls)),
]
