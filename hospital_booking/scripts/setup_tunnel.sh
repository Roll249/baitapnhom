#!/bin/bash
# =================================================================
# Hướng dẫn cấu hình SePay Webhook với ngrok (Development)
# =================================================================
# File này hướng dẫn cách cấu hình để SePay có thể gọi webhook 
# về local development server
# =================================================================

set -e

echo "=============================================="
echo "Hướng dẫn cấu hình SePay Webhook với ngrok"
echo "=============================================="

# Bước 1: Kiểm tra ngrok
echo ""
echo "[Bước 1] Kiểm tra ngrok..."
if command -v ngrok &> /dev/null; then
    ngrok version
else
    echo "ngrok chưa được cài đặt!"
    echo "Hãy cài đặt ngrok:"
    echo "  - Linux: https://ngrok.com/download (tải binary và chmod +x)"
    echo "  - Hoặc:  yay -S ngrok (Arch Linux)"
    echo ""
    echo "Sau khi cài đặt, đăng ký authtoken:"
    echo "  ngrok config add-authtoken YOUR_AUTH_TOKEN"
    exit 1
fi

# Bước 2: Kiểm tra Django server
echo ""
echo "[Bước 2] Kiểm tra Django server..."
PROJECT_DIR="/home/khang/NEU/baitapnhom/hospital_booking"
if [ -d "$PROJECT_DIR" ]; then
    echo "Project directory: $PROJECT_DIR"
else
    echo "Không tìm thấy project directory!"
    exit 1
fi

# Bước 3: Hướng dẫn chạy servers
echo ""
echo "=============================================="
echo "CÁCH THỰC HIỆN"
echo "=============================================="
echo ""
echo "Terminal 1 - Chạy Django server:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python manage.py runserver 8000"
echo ""
echo "Terminal 2 - Chạy ngrok tunnel:"
echo "  ngrok http 8000"
echo ""
echo "Sau khi chạy ngrok, bạn sẽ thấy:"
echo "  Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000"
echo ""
echo "=============================================="
echo "CẤU HÌNH SEPAY DASHBOARD"
echo "=============================================="
echo ""
echo "1. Đăng nhập vào SePay Dashboard"
echo "2. Cấu hình Webhook URL với format:"
echo ""
echo "   https://abc123.ngrok-free.app/payment/sepay/webhook/?token=spsk_live_VatgDg5Vz9o1PRdBpLiK76qk1GCZUkVM"
echo ""
echo "   Thay 'abc123.ngrok-free.app' bằng URL ngrok của bạn"
echo "   Thay 'spsk_live_...' bằng token trong settings.py"
echo ""
echo "=============================================="
echo "KIỂM TRA WEBHOOK"
echo "=============================================="
echo ""
echo "Test webhook bằng curl:"
echo ""
echo 'curl -X POST https://abc123.ngrok-free.app/payment/sepay/webhook/?token=spsk_live_... \'
echo '  -H "Content-Type: application/json" \'
echo '  -d \'{"transferContent": "BILL1", "transferAmount": 100000}\''
echo ""
echo "Kiểm tra logs trong terminal Django:"
echo "  SePay Webhook: Request received from ..."
echo "  SePay Webhook: Found billing #1 ..."
echo "  SePay Webhook: Billing #1 marked as PAID successfully"
echo ""
echo "=============================================="
echo "LƯU Ý QUAN TRỌNG"
echo "=============================================="
echo ""
echo "- ngrok free có thể thay đổi URL sau mỗi lần restart"
echo "- Nếu gặp lỗi 401 Unauthorized, kiểm tra lại token"
echo "- Khi deploy production, nên dùng domain thật với SSL"
echo "- Webhook URL phải là HTTPS để SePay có thể gọi"
echo ""
echo "=============================================="
