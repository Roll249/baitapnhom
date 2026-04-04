# Hệ Thống Đặt Lịch Khám Bệnh Trực Tuyến

## Giới thiệu
Hệ thống hỗ trợ bệnh nhân đặt lịch khám trực tuyến, quản lý lịch làm việc của bác sĩ, và cung cấp công cụ quản lý dữ liệu cho admin - nhằm giảm thời gian chờ đợi, tối ưu hóa quy trình khám chữa bệnh.

## Công nghệ sử dụng
- **Backend**: Django (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript

## Vai trò người dùng

### 🧑‍⚕️ Bệnh nhân
- Đăng ký/đăng nhập
- Xem danh sách bác sĩ theo chuyên khoa
- Xem lịch trống của bác sĩ và đặt lịch
- Hủy lịch trước giờ khám
- Xem lịch sử đặt lịch và trạng thái

### 👨‍⚕️ Bác sĩ
- Đăng nhập, cập nhật thông tin cá nhân
- Xem danh sách lịch được giao
- Duyệt/từ chối/cập nhật trạng thái lịch
- Xem thống kê số bệnh nhân

### 🔐 Admin
- CRUD bác sĩ, bệnh nhân
- Quản lý toàn bộ lịch khám
- Xuất báo cáo: số lượt khám theo bác sĩ/tháng

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
       ↓
[Bác sĩ duyệt → status: confirmed]
       ↓
[Admin xem báo cáo từ appointments]
```

## Tác giả
Nhóm BTN - Đại học Kinh tế Quốc dân (NEU)
