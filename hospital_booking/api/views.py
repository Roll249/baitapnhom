from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q

from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, Specialization
from appointments.models import Appointment, Billing
from notifications.models import Notification
from notifications.services import notify_appointment_created, notify_appointment_confirmed, notify_appointment_cancelled

from .serializers import (
    UserSerializer, UserRegistrationSerializer, DoctorSerializer,
    PatientSerializer, SpecializationSerializer, AppointmentSerializer,
    AppointmentStatusUpdateSerializer, BillingSerializer, NotificationSerializer
)


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'admin' or request.user.is_superuser)


class RegisterView(APIView):
    """Patient registration endpoint"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Đăng ký thành công',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """User profile endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecializationViewSet(viewsets.ReadOnlyModelViewSet):
    """Specialization list endpoint"""
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.AllowAny]


class DoctorViewSet(viewsets.ReadOnlyModelViewSet):
    """Doctor list and detail endpoint"""
    queryset = Doctor.objects.filter(status='available')
    serializer_class = DoctorSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Doctor.objects.filter(status='available')
        specialization = self.request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization_id=specialization)
        return queryset


class PatientAppointmentViewSet(viewsets.ModelViewSet):
    """Patient appointment management"""
    serializer_class = AppointmentSerializer
    permission_classes = [IsPatient]
    
    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user.patient_profile)
    
    def perform_create(self, serializer):
        appointment = serializer.save(patient=self.request.user.patient_profile, status='pending')
        notify_appointment_created(appointment)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status in ['pending', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.save()
            notify_appointment_cancelled(appointment, 'patient')
            return Response({'message': 'Đã hủy lịch hẹn'})
        return Response({'error': 'Không thể hủy lịch hẹn này'}, status=status.HTTP_400_BAD_REQUEST)


class DoctorAppointmentViewSet(viewsets.ModelViewSet):
    """Doctor appointment management"""
    serializer_class = AppointmentSerializer
    permission_classes = [IsDoctor]
    
    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user.doctor_profile)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'pending':
            appointment.status = 'confirmed'
            appointment.save()
            notify_appointment_confirmed(appointment)
            return Response({'message': 'Đã xác nhận lịch hẹn'})
        return Response({'error': 'Không thể xác nhận lịch hẹn này'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'pending':
            appointment.status = 'rejected'
            appointment.save()
            notify_appointment_cancelled(appointment, 'doctor')
            return Response({'message': 'Đã từ chối lịch hẹn'})
        return Response({'error': 'Không thể từ chối lịch hẹn này'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status == 'confirmed':
            appointment.status = 'completed'
            appointment.notes = request.data.get('notes', '')
            appointment.save()
            
            # Create billing
            Billing.objects.create(
                appointment=appointment,
                amount=appointment.doctor.consultation_fee
            )
            return Response({'message': 'Đã hoàn thành lịch hẹn'})
        return Response({'error': 'Không thể hoàn thành lịch hẹn này'}, status=status.HTTP_400_BAD_REQUEST)


class NotificationViewSet(viewsets.ModelViewSet):
    """User notification management"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Đã đánh dấu đã đọc'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'Đã đánh dấu tất cả là đã đọc'})
