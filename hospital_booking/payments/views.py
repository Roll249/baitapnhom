import json
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from appointments.models import Billing
from notifications.services import notify_payment_success
from .vnpay import VNPayService
from .sepay import SePayService


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
    """Create SePay QR checkout for a billing."""
    billing = get_object_or_404(Billing, id=billing_id)
    
    # Check if user owns this billing
    if billing.appointment.patient.user != request.user:
        messages.error(request, 'Bạn không có quyền thanh toán hóa đơn này.')
        return redirect('my_appointments')
    
    # Check if already paid
    if billing.payment_status == 'paid':
        messages.info(request, 'Hóa đơn này đã được thanh toán.')
        return redirect('my_appointments')
    
    sepay = SePayService()
    checkout_data = sepay.build_checkout_data(billing)

    if not checkout_data['bank_code'] or not checkout_data['account_number']:
        messages.error(request, 'Cấu hình SePay chưa đầy đủ. Vui lòng liên hệ quản trị viên.')
        return redirect('payment_history')

    context = {
        'billing': billing,
        'checkout_data': checkout_data,
    }
    return render(request, 'payments/sepay_checkout.html', context)


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


def _extract_billing_id_from_content(transfer_content):
    """Extract billing id from transfer content in format BILL{id}."""
    match = re.search(r'BILL(\d+)', transfer_content or '', re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


@csrf_exempt
@require_http_methods(["POST"])
def sepay_webhook(request):
    """Handle webhook from SePay and mark billing paid when transfer is valid."""
    expected_secret = getattr(settings, 'SEPAY_WEBHOOK_SECRET', '')
    if expected_secret:
        auth_header = request.headers.get('Authorization', '')
        bearer_token = auth_header.replace('Bearer ', '').strip() if auth_header else ''
        webhook_token = bearer_token or request.headers.get('X-Webhook-Token', '') or request.GET.get('token', '')
        if webhook_token != expected_secret:
            return JsonResponse({'success': False, 'message': 'Unauthorized webhook'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({'success': False, 'message': 'Payload must be a JSON object'}, status=400)

    normalized = SePayService.normalize_webhook_payload(payload)
    billing_id = _extract_billing_id_from_content(normalized['transfer_content'])

    if not billing_id:
        return JsonResponse({'success': False, 'message': 'Billing reference not found'}, status=400)

    billing = Billing.objects.filter(id=billing_id).select_related('appointment__patient__user').first()
    if not billing:
        return JsonResponse({'success': False, 'message': 'Billing not found'}, status=404)

    if billing.payment_status == 'paid':
        return JsonResponse({'success': True, 'message': 'Billing already paid'})

    if normalized['amount'] < billing.amount:
        return JsonResponse({'success': False, 'message': 'Transferred amount is less than billing amount'}, status=400)

    billing.payment_status = 'paid'
    billing.payment_date = timezone.now()
    billing.payment_method = 'SePay'
    billing.save(update_fields=['payment_status', 'payment_date', 'payment_method'])

    notify_payment_success(billing)

    return JsonResponse({'success': True, 'message': 'Payment confirmed'})


@login_required
def payment_status(request, billing_id):
    """Return payment status for current patient's billing."""
    billing = get_object_or_404(Billing, id=billing_id)

    if billing.appointment.patient.user != request.user:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)

    return JsonResponse(
        {
            'success': True,
            'billing_id': billing.id,
            'payment_status': billing.payment_status,
            'is_paid': billing.payment_status == 'paid',
        }
    )


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
