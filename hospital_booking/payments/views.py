from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from appointments.models import Billing
from notifications.services import notify_payment_success
from .vnpay import VNPayService


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def create_payment(request, billing_id):
    """Create VNPay payment for a billing"""
    billing = get_object_or_404(Billing, id=billing_id)
    
    # Check if user owns this billing
    if billing.appointment.patient.user != request.user:
        messages.error(request, 'Bạn không có quyền thanh toán hóa đơn này.')
        return redirect('my_appointments')
    
    # Check if already paid
    if billing.payment_status == 'paid':
        messages.info(request, 'Hóa đơn này đã được thanh toán.')
        return redirect('my_appointments')
    
    vnpay = VNPayService()
    
    order_id = f"BILL{billing.id}_{int(timezone.now().timestamp())}"
    order_desc = f"Thanh toan lich kham #{billing.appointment.id}"
    ip_addr = get_client_ip(request)
    
    payment_url = vnpay.create_payment_url(
        order_id=order_id,
        amount=billing.amount,
        order_desc=order_desc,
        ip_addr=ip_addr
    )
    
    return redirect(payment_url)


def vnpay_return(request):
    """Handle VNPay payment return"""
    vnpay = VNPayService()
    
    response_data = dict(request.GET)
    # Flatten the dict (GET params are lists)
    response_data = {k: v[0] if isinstance(v, list) else v for k, v in response_data.items()}
    
    if vnpay.verify_response(response_data):
        vnp_ResponseCode = response_data.get('vnp_ResponseCode', '')
        vnp_TxnRef = response_data.get('vnp_TxnRef', '')
        
        # Extract billing ID from order reference
        try:
            billing_id = int(vnp_TxnRef.split('_')[0].replace('BILL', ''))
            billing = Billing.objects.get(id=billing_id)
        except (ValueError, Billing.DoesNotExist):
            messages.error(request, 'Không tìm thấy hóa đơn.')
            return redirect('home')
        
        if vnp_ResponseCode == '00':
            # Payment successful
            billing.payment_status = 'paid'
            billing.payment_date = timezone.now()
            billing.payment_method = 'VNPay'
            billing.save()
            
            notify_payment_success(billing)
            
            messages.success(request, f'Thanh toán thành công! Số tiền: {billing.amount:,.0f} VNĐ')
        else:
            messages.error(request, 'Thanh toán không thành công. Vui lòng thử lại.')
    else:
        messages.error(request, 'Chữ ký không hợp lệ. Giao dịch bị từ chối.')
    
    return redirect('my_appointments')


@login_required
def payment_history(request):
    """View payment history"""
    if request.user.is_patient():
        billings = Billing.objects.filter(
            appointment__patient=request.user.patient_profile
        ).order_by('-created_at')
    else:
        billings = Billing.objects.none()
    
    return render(request, 'payments/history.html', {'billings': billings})
