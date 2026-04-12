# Hệ Thống Đặt Lịch Khám Bệnh Trực Tuyến

## Giới thiệu

Hệ thống hỗ trợ bệnh nhân đặt lịch khám trực tuyến, quản lý lịch làm việc của bác sĩ, và cung cấp công cụ quản lý dữ liệu cho admin — nhằm giảm thời gian chờ đợi, tối ưu hóa quy trình khám chữa bệnh.

---

## Mục lục

1. [Công nghệ sử dụng](#1-công-nghệ-sử-dụng)
2. [Tính năng chính](#2-tính-năng-chính)
3. [Cài đặt và chạy](#3-cài-đặt-và-chạy)
4. [Cấu hình](#4-cấu-hình)
5. [Tài khoản mẫu](#5-tài-khoản-mẫu)
6. [Cấu trúc project](#6-cấu-trúc-project)
7. [API Endpoints](#7-api-endpoints)
8. [Luồng dữ liệu](#8-luồng-dữ-liệu)
9. [Hướng dẫn thanh toán SePay QR](#9-hướng-dẫn-thanh-toán-sepay-qr)
10. [Hướng dẫn thanh toán VNPay](#10-hướng-dẫn-thanh-toán-vnpay)
11. [Cấu hình webhook cho SePay](#11-cấu-hình-webhook-cho-sepay)

---

## 1. Công nghệ sử dụng

| Thành phần | Công nghệ | Mô tả |
|-----------|-----------|-------|
| Backend | Django 6.0 + Django REST Framework | Python web framework |
| Database | SQLite (dev) / PostgreSQL (prod) | ORM qua Django |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript | Giao diện responsive |
| Authentication | Session-based + JWT | Bảo mật đa cấp |
| Payment | SePay QR Code + VNPay | Thanh toán QR VN |
| API | REST API + SimpleJWT | Truy cập qua token |

---

## 2. Tính năng chính

### 2.1. Bệnh nhân

- Đăng ký / Đăng nhập tài khoản
- Xem danh sách bác sĩ theo chuyên khoa
- Xem lịch trống của bác sĩ
- Đặt lịch khám với ngày giờ cụ thể
- Hủy lịch trước giờ khám
- Xem lịch sử đặt lịch và trạng thái
- Thanh toán online qua SePay QR hoặc VNPay
- Nhận thông báo email khi có cập nhật

### 2.2. Bác sĩ

- Đăng nhập, cập nhật thông tin cá nhân
- Xem danh sách lịch khám được giao
- Duyệt / Từ chối / Cập nhật trạng thái lịch hẹn
- Xem thống kê số bệnh nhân
- Nhận thông báo khi có lịch hẹn mới

### 2.3. Quản trị viên (Admin)

- CRUD bác sĩ và bệnh nhân
- Quản lý toàn bộ lịch khám
- Dashboard thống kê tổng quan
- Xuất báo cáo số lượt khám theo bác sĩ / tháng
- Quản lý chuyên khoa

### 2.4. Bảo mật

- JWT Authentication cho REST API
- Session-based cho web
- Rate Limiting: 100 req/giờ (anonymous), 1000 req/giờ (authenticated)
- CORS protection
- CSRF protection

### 2.5. Thông báo

- Email thông báo khi đặt lịch / xác nhận / thanh toán
- Lưu log email vào file
- Thông báo in-app qua messages framework

---

## 3. Cài đặt và chạy

### 3.1. Yêu cầu hệ thống

- Python 3.10+
- pip
- Git

### 3.2. Các bước cài đặt

```bash
# 1. Di chuyển vào thư mục project
cd hospital_booking

# 2. Tạo virtual environment
python -m venv venv

# 3. Kích hoạt virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Cài đặt dependencies
pip install -r requirements.txt

# 5. Chạy migrations
python manage.py migrate

# 6. Tạo dữ liệu mẫu
python create_sample_data.py

# 7. Chạy server
python manage.py runserver
```

### 3.3. Truy cập

- Website: http://127.0.0.1:8000
- Admin Panel: http://127.0.0.1:8000/admin
- API Documentation: http://127.0.0.1:8000/api/

---

## 4. Cấu hình

### 4.1. File `.env` (khuyến nghị)

Tạo file `.env` trong thư mục `hospital_booking/`:

```env
# Django settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# SePay Configuration
SEPAY_BANK_CODE=MBBank
SEPAY_ACCOUNT_NUMBER=0982079321
SEPAY_ACCOUNT_NAME=LE QUYNH TRANG
SEPAY_QR_TEMPLATE=compact2
SEPAY_WEBHOOK_SECRET=your-webhook-secret
SEPAY_REQUIRE_WEBHOOK_TOKEN=True

# VNPay Configuration
VNPAY_TMN_CODE=your-terminal-code
VNPAY_HASH_SECRET_KEY=your-secret-key

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 4.2. Cấu hình trong `settings.py`

#### Email (Gmail SMTP)

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # App password từ Google
DEFAULT_FROM_EMAIL = 'HealthCare <noreply@healthcare.com>'
```

Để lấy App Password từ Google:
1. Đăng nhập Google Account
2. Vào Security > 2-Step Verification (bật trước)
3. Vào Security > App passwords
4. Tạo App password mới và copy

#### SePay QR Code

```python
SEPAY_BANK_CODE = 'MBBank'           # Mã ngân hàng (MBBank, ACB, VCB,...)
SEPAY_ACCOUNT_NUMBER = '0982079321'   # Số tài khoản
SEPAY_ACCOUNT_NAME = 'LE QUYNH TRANG' # Tên chủ tài khoản
SEPAY_QR_TEMPLATE = 'compact2'       # Template QR (compact1, compact2,...)
SEPAY_WEBHOOK_SECRET = 'your-secret' # Secret cho webhook
SEPAY_WEBHOOK_URL = 'https://your-domain.com/payment/sepay/webhook/'
```

#### VNPay

```python
VNPAY_TMN_CODE = 'your-terminal-code'      # Terminal code từ VNPay
VNPAY_HASH_SECRET_KEY = 'your-secret-key'  # Secret key từ VNPay
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = 'http://localhost:8000/payment/vnpay-return/'
```

---

## 5. Tài khoản mẫu

| Vai trò | Username | Password | Link đăng nhập |
|---------|----------|----------|----------------|
| Admin | admin | admin123 | /admin |
| Bác sĩ 1 | doctor1 | doctor123 | /login |
| Bác sĩ 2 | doctor2 | doctor123 | /login |
| Bác sĩ 3 | doctor3 | doctor123 | /login |
| Bác sĩ 4 | doctor4 | doctor123 | /login |
| Bệnh nhân | patient1 | patient123 | /login |

Sau khi chạy `python create_sample_data.py`, các tài khoản trên sẽ được tạo tự động.

---

## 6. Cấu trúc project

```
hospital_booking/
├── manage.py                          # Django CLI
├── create_sample_data.py              # Script tạo dữ liệu mẫu
├── requirements.txt                   # Dependencies
├── db.sqlite3                        # Database SQLite
├── core/                             # Cấu hình Django core
│   ├── settings.py                   # Settings chính
│   ├── urls.py                       # URL chính
│   ├── wsgi.py                       # WSGI config
│   └── asgi.py                       # ASGI config
├── accounts/                         # Authentication, User model
│   ├── models.py                     # Custom User model (patient/doctor/admin)
│   ├── views.py                     # Login, Register, Profile
│   ├── forms.py                     # Form đăng ký
│   ├── urls.py                       # URL routes
│   └── admin.py                     # Admin registration
├── patients/                        # Patient module
│   ├── models.py                     # Patient profile
│   ├── views.py                     # Booking, doctor list
│   ├── urls.py                      # URL routes
│   └── admin.py                     # Admin registration
├── doctors/                         # Doctor module
│   ├── models.py                     # Doctor, Specialization, Schedule
│   ├── views.py                     # Dashboard, appointments
│   ├── urls.py                       # URL routes
│   └── admin.py                     # Admin registration
├── appointments/                    # Appointment module
│   ├── models.py                     # Appointment, Billing
│   ├── views.py                     # Admin views
│   ├── urls.py                       # URL routes
│   ├── admin.py                     # Admin registration
│   └── migrations/                  # Database migrations
├── notifications/                   # Email notifications
│   ├── models.py                     # Notification models
│   ├── views.py                     # Notification views
│   ├── services.py                  # Email sending service
│   ├── urls.py                       # URL routes
│   └── templates/                   # Email templates
│       └── email/
│           ├── appointment_new.html
│           ├── appointment_confirmed.html
│           └── payment_success.html
├── payments/                        # Payment integration
│   ├── views.py                     # Payment views, webhook handlers
│   ├── urls.py                       # URL routes
│   ├── sepay.py                    # SePay QR service
│   └── vnpay.py                    # VNPay service
├── api/                            # REST API
│   ├── views.py                     # API views
│   ├── serializers.py               # DRF serializers
│   └── urls.py                       # API routes
├── templates/                      # HTML templates
│   ├── base.html                    # Base template
│   ├── home.html                   # Trang chủ
│   ├── accounts/                   # Auth templates
│   ├── patients/                   # Patient templates
│   ├── doctors/                    # Doctor templates
│   ├── admin_panel/                # Admin templates
│   ├── payments/                   # Payment templates
│   └── notifications/              # Notification templates
├── static/                         # Static files
│   ├── css/                        # Custom CSS
│   ├── js/                         # Custom JavaScript
│   └── images/                     # Images
└── logs/                           # Log files
    └── debug.log                   # Debug logs
```

---

## 7. API Endpoints

### 7.1. Authentication

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/api/token/` | Lấy JWT access + refresh token |
| POST | `/api/token/refresh/` | Refresh access token |
| POST | `/api/register/` | Đăng ký bệnh nhân mới |

**Ví dụ đăng nhập:**

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "patient1", "password": "patient123"}'
```

**Response:**

```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

### 7.2. Doctors API

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/doctors/` | Danh sách tất cả bác sĩ |
| GET | `/api/doctors/{id}/` | Chi tiết bác sĩ |
| GET | `/api/specializations/` | Danh sách chuyên khoa |
| GET | `/api/doctors/{id}/available-slots/` | Lịch trống của bác sĩ |

### 7.3. Appointments API (Patient)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/patient/appointments/` | Lịch hẹn của bệnh nhân |
| POST | `/api/patient/appointments/` | Đặt lịch mới |
| GET | `/api/patient/appointments/{id}/` | Chi tiết lịch hẹn |
| POST | `/api/patient/appointments/{id}/cancel/` | Hủy lịch |

**Ví dụ đặt lịch:**

```bash
curl -X POST http://localhost:8000/api/patient/appointments/ \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 1,
    "appointment_date": "2026-04-15",
    "time_slot": "09:00",
    "reason": "Khám định kỳ"
  }'
```

### 7.4. Appointments API (Doctor)

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/doctor/appointments/` | Lịch h���n của bác sĩ |
| GET | `/api/doctor/appointments/{id}/` | Chi tiết lịch hẹn |
| POST | `/api/doctor/appointments/{id}/confirm/` | Xác nhận lịch |
| POST | `/api/doctor/appointments/{id}/reject/` | Từ chối lịch |
| POST | `/api/doctor/appointments/{id}/complete/` | Hoàn thành lịch |

### 7.5. Payments API

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/patient/billings/` | Danh sách hóa đơn |
| GET | `/api/patient/billings/{id}/` | Chi tiết hóa đơn |

---

## 8. Luồng dữ liệu

```
┌──────────────────────────────────────────────────────────────────────┐
│                          LUỒNG ĐẶT LỊCH KHÁM                          │
└──────────────────────────────────────────────────────────────────────┘

[Bệnh nhân đăng ký/đăng nhập]
           │
           ▼
[Chọn chuyên khoa → Chọn bác sĩ → Chọn ngày giờ]
           │
           ▼
[Tạo Appointment (status: PENDING)]
           │
           ├──────────────────┬──────────────────┐
           ▼                  ▼                  ▼
    📧 Email thông báo   📧 Email thông báo   📧 SMS (tùy chọn)
    cho bác sĩ           cho bệnh nhân


[Bác sĩ duyệt lịch]
           │
           ├──────────────────┬──────────────────┐
           ▼                  ▼                  ▼
    Status: CONFIRMED   Status: REJECTED   Status: CANCELLED
           │                  │                  │
           ▼                  ▼                  ▼
    [Bệnh nhân thanh toán]  [Bệnh nhân nhận     [Bệnh nhân nhận
     qua SePay QR/VNPay]    thông báo từ chối]   thông báo hủy]


[Thanh toán thành công]
           │
           ▼
[Billing status: PAID]
           │
           ▼
    📧 Email xác nhận thanh toán cho bệnh nhân


[Admin xem báo cáo thống kê]
           │
           ▼
[Xuất báo cáo theo bác sĩ/tháng]
```

---

## 9. Hướng dẫn thanh toán SePay QR

### 9.1. SePay là gì?

SePay là dịch vụ hỗ trợ thanh toán QR bằng tài khoản ngân hàng. Khách hàng quét QR code và chuyển khoản theo nội dung chuyển tiền được chỉ định. Hệ thống tự động nhận biết thanh toán qua webhook.

### 9.2. Cách hoạt động

1. Bệnh nhân đặt lịch → Hệ thống tạo Billing (status: pending)
2. Bệnh nhân chọn "Thanh toán SePay QR"
3. Hệ thống hiển thị QR code với nội dung `BILL{id}`
4. Bệnh nhân quét QR bằng app ngân hàng và chuyển tiền
5. SePay gửi webhook về server khi có chuyển khoản
6. Hệ thống tự động cập nhật Billing status → PAID

### 9.3. Cấu hình SePay

```python
# settings.py
SEPAY_BANK_CODE = 'MBBank'           # Mã ngân hàng
SEPAY_ACCOUNT_NUMBER = '0982079321'   # Số tài khoản
SEPAY_ACCOUNT_NAME = 'LE QUYNH TRANG' # Tên chủ tài khoản
SEPAY_QR_TEMPLATE = 'compact2'       # Template QR
SEPAY_WEBHOOK_SECRET = 'your-secret' # Webhook secret token
```

---

## 10. Hướng dẫn thanh toán VNPay

### 10.1. VNPay là gì?

VNPay là cổng thanh toán trực tuyến phổ biến tại Việt Nam. Hỗ trợ thanh toán qua nhiều ngân hàng và ví điện tử.

### 10.2. Cách hoạt động

1. Bệnh nhân đặt lịch → Hệ thống tạo Billing (status: pending)
2. Bệnh nhân chọn "Thanh toán VNPay"
3. Hệ thống redirect sang VNPay sandbox
4. Bệnh nhân hoàn tất thanh toán trên VNPay
5. VNPay redirect về website với kết quả
6. Hệ thống xác minh signature và cập nhật Billing status

### 10.3. Cấu hình VNPay

```python
# settings.py
VNPAY_TMN_CODE = 'your-terminal-code'
VNPAY_HASH_SECRET_KEY = 'your-secret-key'
VNPAY_PAYMENT_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = 'http://localhost:8000/payment/vnpay-return/'
```

### 10.4. Lưu ý

- Sử dụng `VNPAY_PAYMENT_URL` với sandbox URL cho development
- Thay đổi sang URL production khi deploy

---

## 11. Cấu hình webhook cho SePay

### 11.1. Tại sao cần webhook?

SePay cần gọi webhook về server để thông báo khi có chuyển khoản. Server phải có public URL để SePay có thể gọi đến.

### 11.2. Development với ngrok

**Bước 1: Cài đặt ngrok**

```bash
# Linux - tải binary từ trang chủ
# Hoặc Arch Linux:
yay -S ngrok

# Đăng ký authtoken
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

**Bước 2: Chạy servers**

```bash
# Terminal 1: Chạy Django server
cd hospital_booking
source venv/bin/activate
python manage.py runserver 8000

# Terminal 2: Chạy ngrok
ngrok http 8000
```

**Bước 3: Cấu hình SePay Dashboard**

1. Đăng nhập SePay Dashboard
2. Vào cài đặt Webhook
3. Thêm Webhook URL:

```
https://abc123.ngrok-free.app/payment/sepay/webhook/?token=spsk_live_...
```

Thay `abc123.ngrok-free.app` bằng URL ngrok của bạn (không có `http://`).

### 11.3. Production

Khi deploy production:
1. Sử dụng domain thật có SSL (HTTPS)
2. Cập nhật `SEPAY_WEBHOOK_URL` trong settings
3. Disable `SEPAY_REQUIRE_WEBHOOK_TOKEN` nếu không cần token

### 11.4. Kiểm tra webhook

```bash
# Test webhook bằng curl
curl -X POST https://abc123.ngrok-free.app/payment/sepay/webhook/?token=spsk_live_... \
  -H "Content-Type: application/json" \
  -d '{
    "transferContent": "BILL1",
    "transferAmount": 200000,
    "id": "TXN123456"
  }'
```

Kiểm tra log trong terminal Django:

```
SePay Webhook: Request received from ...
SePay Webhook: Found billing #1 ...
SePay Webhook: Billing #1 marked as PAID successfully
```

---

## 12. Xem log

Logs được lưu tại `logs/debug.log`:

```bash
# Xem log real-time
tail -f logs/debug.log

# Hoặc xem toàn bộ
cat logs/debug.log
```

Log ghi lại:
- Webhook requests từ SePay
- Thông tin thanh toán
- Lỗi và cảnh báo

---

## 13. Troubleshooting

### Lỗi "Email authentication failed"

- Kiểm tra `EMAIL_HOST_USER` và `EMAIL_HOST_PASSWORD`
- Đảm bảo đã bật 2-Step Verification trên Google
- Tạo App Password mới từ Google Account

### Lỗi "Webhook token unauthorized"

- Kiểm tra `SEPAY_WEBHOOK_SECRET` trong settings.py
- Đảm bảo token trong URL webhook khớp với settings
- Kiểm tra format URL: `?token=spsk_live_...` (không có Bearer prefix)

### Lỗi "Billing not found"

- Kiểm tra `transferContent` trong webhook payload phải format `BILL{id}`
- Kiểm tra billing có tồn tại trong database

### Lỗi "Amount mismatch"

- Số tiền chuyển khoản phải >= số tiền billing
- Kiểm tra đơn vị tiền tệ (VNĐ)

### Lỗi "CSRF verification failed"

- Đảm bảo có `@csrf_exempt` decorator cho webhook views
- Kiểm tra CSRF token cho form submissions

### Lỗi "Connection refused" khi gửi email

- Kiểm tra kết nối internet
- Kiểm tra cấu hình SMTP
- Thử tắt tạm thời EMAIL_USE_TLS và dùng EMAIL_USE_SSL

---

## 14. Deploy Production

### 14.1. Yêu cầu

- Domain có SSL certificate
- PostgreSQL database
- Nginx web server
- Gunicorn hoặc uWSGI
- Redis (tùy chọn cho caching)

### 14.2. Cấu hình PostgreSQL

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hospital_booking',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 14.3. Gunicorn

```bash
pip install gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### 14.4. Nginx config

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

---

## Tác giả

**Nhóm BTN** - Đại học Kinh tế Quốc dân (NEU)

Môn Lập trình Web - Bài tập nhóm

---

## Giấy phép

MIT License
