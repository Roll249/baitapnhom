from rest_framework import serializers
from accounts.models import User
from patients.models import Patient
from doctors.models import Doctor, Specialization, DoctorSchedule
from appointments.models import Appointment, Billing
from notifications.models import Notification


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role']
        read_only_fields = ['id', 'role']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Mật khẩu không khớp'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role='patient'
        )
        Patient.objects.create(user=user)
        return user


class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description']


class DoctorScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = ['id', 'weekday', 'weekday_display', 'start_time', 'end_time', 'max_patients', 'is_active']


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specialization = SpecializationSerializer(read_only=True)
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'specialization', 'qualification', 'experience_years', 
                  'consultation_fee', 'status', 'bio', 'schedules', 'full_name']
    
    def get_full_name(self, obj):
        return str(obj)


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = ['id', 'user', 'date_of_birth', 'gender', 'insurance_info', 'medical_history', 'full_name']
    
    def get_full_name(self, obj):
        return str(obj)


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all(), source='doctor', write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'doctor_id', 'appointment_date', 'appointment_time',
                  'status', 'status_display', 'symptoms', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'patient', 'status', 'notes', 'created_at', 'updated_at']


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']


class BillingSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = Billing
        fields = ['id', 'appointment', 'amount', 'payment_status', 'payment_status_display', 
                  'payment_date', 'payment_method', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'link', 'is_read', 'created_at']
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'link', 'created_at']
