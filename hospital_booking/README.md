# Hệ Thống Đặt Lịch Khám Bệnh Trực Tuyến

## Giới thiệu
Hệ thống hỗ trợ bệnh nhân đặt lịch khám trực tuyến, quản lý lịch làm việc của bác sĩ, và cung cấp công cụ quản lý dữ liệu cho admin - nhằm giảm thời gian chờ đợi, tối ưu hóa quy trình khám chữa bệnh.

## Công nghệ sử dụng
- **Backend**: Django (Python) + Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Authentication**: Session-based + JWT (API)
- **Payment**: SePay QR + VNPay Integration

## Tính năng chính

### 🧑‍⚕️ Bệnh nhân
- Đăng ký/đăng nhập
- Xem danh sách bác sĩ theo chuyên khoa
- Xem lịch trống của bác sĩ và đặt lịch
- Hủy lịch trước giờ khám
- Xem lịch sử đặt lịch và trạng thái
- **Thanh toán online qua SePay QR / VNPay**
- **Nhận thông báo email & in-app**

### 👨‍⚕️ Bác sĩ
- Đăng nhập, cập nhật thông tin cá nhân
- Xem danh sách lịch được giao
- Duyệt/từ chối/cập nhật trạng thái lịch
- Xem thống kê số bệnh nhân
- **Nhận thông báo khi có lịch hẹn mới**

### 🔐 Admin
- CRUD bác sĩ, bệnh nhân
- Quản lý toàn bộ lịch khám
- Xuất báo cáo: số lượt khám theo bác sĩ/tháng

### 🔒 Bảo mật
- JWT Authentication cho REST API
- Rate Limiting (100 req/hour anonymous, 1000 req/hour authenticated)
- CORS protection
- CSRF protection

### 🔔 Thông báo
- Email thông báo khi đặt lịch/xác nhận/thanh toán
- Thông báo in-app real-time
- Lưu log email

## Cài đặt và chạy

### 1. Clone và cài đặt dependencies
```bash
cd hospital_booking
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Chạy migrations
```bash
python manage.py migrate
```

### 3. Tạo dữ liệu mẫu
```bash
python create_sample_data.py
```

### 4. Chạy server
```bash
python manage.py runserver
```

Truy cập: http://127.0.0.1:8000

## Cấu hình

### Email (settings.py)
```python
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### SePay QR (settings.py)
```python
SEPAY_BANK_CODE = 'your-bank-code'
SEPAY_ACCOUNT_NUMBER = 'your-account-number'
SEPAY_ACCOUNT_NAME = 'your-account-name'
SEPAY_WEBHOOK_SECRET = 'your-webhook-secret'
```

### VNPay (settings.py)
```python
VNPAY_TMN_CODE = 'your-terminal-code'
VNPAY_HASH_SECRET_KEY = 'your-secret-key'
```

## API Endpoints

### Authentication
- `POST /api/token/` - Lấy JWT token
- `POST /api/token/refresh/` - Refresh token
- `POST /api/register/` - Đăng ký bệnh nhân

### Doctors
- `GET /api/doctors/` - Danh sách bác sĩ
- `GET /api/specializations/` - Danh sách chuyên khoa

### Appointments (Patient)
- `GET /api/patient/appointments/` - Lịch hẹn của bệnh nhân
- `POST /api/patient/appointments/` - Đặt lịch mới
- `POST /api/patient/appointments/{id}/cancel/` - Hủy lịch

### Appointments (Doctor)
- `GET /api/doctor/appointments/` - Lịch hẹn của bác sĩ
- `POST /api/doctor/appointments/{id}/confirm/` - Xác nhận
- `POST /api/doctor/appointments/{id}/reject/` - Từ chối
- `POST /api/doctor/appointments/{id}/complete/` - Hoàn thành

## Tài khoản mẫu

| Vai trò | Username | Password |
|---------|----------|----------|
| Admin | admin | admin123 |
| Bác sĩ | doctor1 | doctor123 |
| Bác sĩ | doctor2 | doctor123 |
| Bệnh nhân | patient1 | patient123 |

## Cấu trúc project

```
hospital_booking/
├── manage.py
├── core/               # Settings, URLs chính
├── accounts/           # Authentication, User model
├── patients/           # Patient profile, booking logic
├── doctors/            # Doctor profile, schedule
├── appointments/       # Appointment model, Admin views
├── notifications/      # ✨ Email & in-app notifications
├── payments/           # ✨ VNPay integration
├── api/                # ✨ REST API với JWT
├── templates/          # HTML templates
├── static/             # CSS, JS, images
└── requirements.txt
```

## Luồng dữ liệu

```
[Bệnh nhân đăng ký]
       ↓
[Chọn bác sĩ + khung giờ]
       ↓
[Tạo appointment (status: pending)]
       ↓ 📧 Email thông báo cho bác sĩ
[Bác sĩ duyệt → status: confirmed]
       ↓ 📧 Email xác nhận cho bệnh nhân
[Bệnh nhân thanh toán qua SePay QR / VNPay]
       ↓ 📧 Email xác nhận thanh toán
[Admin xem báo cáo từ appointments]
```

## Tác giả
Nhóm BTN - Đại học Kinh tế Quốc dân (NEU)
