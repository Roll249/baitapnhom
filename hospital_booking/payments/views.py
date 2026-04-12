import json
import logging
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


logger = logging.getLogger(__name__)


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
    """
    Handle webhook from SePay and mark billing paid when transfer is valid.
    
    IMPORTANT: Để webhook hoạt động, server phải có public URL:
    - Development: Sử dụng ngrok: `ngrok http 8000`
    - Production: Deploy lên server có domain và SSL
    
    SePay sẽ gửi POST request đến URL webhook đã cấu hình trong SePay Dashboard.
    """
    logger.info('='*60)
    logger.info('SePay Webhook: Request received from %s', get_client_ip(request))
    logger.debug('SePay Webhook: Headers=%s', dict(request.headers))
    
    expected_secret = getattr(settings, 'SEPAY_WEBHOOK_SECRET', '')
    require_token = getattr(settings, 'SEPAY_REQUIRE_WEBHOOK_TOKEN', False)

    raw_auth = request.headers.get('Authorization', '')
    auth_token = raw_auth.strip()
    for prefix in ['Bearer ', 'Apikey ', 'Token ']:
        if raw_auth.startswith(prefix):
            auth_token = raw_auth.replace(prefix, '', 1).strip()
            break

    provided_tokens = [
        auth_token,
        request.headers.get('X-Webhook-Token', '').strip(),
        request.headers.get('X-Sepay-Token', '').strip(),
        request.GET.get('token', '').strip(),
    ]
    provided_tokens = [token for token in provided_tokens if token]
    
    logger.debug('SePay Webhook: Provided tokens count=%d', len(provided_tokens))

    if expected_secret:
        if provided_tokens and expected_secret not in provided_tokens:
            logger.warning('SePay Webhook: Unauthorized - invalid token provided')
            return JsonResponse({'success': False, 'message': 'Unauthorized webhook'}, status=401)
        if require_token and not provided_tokens:
            logger.warning('SePay Webhook: Unauthorized - token required but not provided')
            return JsonResponse({'success': False, 'message': 'Webhook token is required'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
        logger.debug('SePay Webhook: Raw payload=%s', payload)
    except json.JSONDecodeError as e:
        logger.error('SePay Webhook: Invalid JSON payload - %s', e)
        return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)

    if not isinstance(payload, dict):
        logger.error('SePay Webhook: Payload must be a JSON object')
        return JsonResponse({'success': False, 'message': 'Payload must be a JSON object'}, status=400)

    payload_data = payload.get('data')
    if isinstance(payload_data, dict):
        payload = payload_data
        logger.debug('SePay Webhook: Unwrapped nested payload')

    body_token = str(payload.get('token', '')).strip()
    if expected_secret and body_token:
        if body_token != expected_secret:
            logger.warning('SePay Webhook: Unauthorized - invalid token in body')
            return JsonResponse({'success': False, 'message': 'Unauthorized webhook'}, status=401)

    normalized = SePayService.normalize_webhook_payload(payload)
    logger.info('SePay Webhook: Normalized data - transfer_content=%s, amount=%s', 
               normalized['transfer_content'], normalized['amount'])
    
    billing_id = _extract_billing_id_from_content(normalized['transfer_content'])

    if not billing_id:
        logger.warning('SePay Webhook: Missing BILL reference in transfer_content="%s"', 
                       normalized['transfer_content'])
        return JsonResponse({'success': False, 'message': 'Billing reference not found'}, status=400)

    billing = Billing.objects.filter(id=billing_id).select_related('appointment__patient__user').first()
    if not billing:
        logger.warning('SePay Webhook: Billing not found. billing_id=%s', billing_id)
        return JsonResponse({'success': False, 'message': 'Billing not found'}, status=404)

    logger.info('SePay Webhook: Found billing #%s - current status=%s, expected amount=%s, received amount=%s',
                billing_id, billing.payment_status, billing.amount, normalized['amount'])

    if billing.payment_status == 'paid':
        logger.info('SePay Webhook: Billing #%s already paid, skipping', billing_id)
        return JsonResponse({'success': True, 'message': 'Billing already paid'})

    if normalized['amount'] < billing.amount:
        logger.warning(
            'SePay Webhook: Amount mismatch for billing #%s - expected=%s, got=%s',
            billing_id, billing.amount, normalized['amount']
        )
        return JsonResponse({'success': False, 'message': 'Transferred amount is less than billing amount'}, status=400)

    billing.payment_status = 'paid'
    billing.payment_date = timezone.now()
    billing.payment_method = 'SePay'
    if normalized.get('transaction_code'):
        billing.transaction_id = normalized['transaction_code']
    billing.save(update_fields=['payment_status', 'payment_date', 'payment_method', 'transaction_id'])
    
    logger.info('SePay Webhook: Billing #%s marked as PAID successfully', billing_id)

    try:
        notify_payment_success(billing)
        logger.info('SePay Webhook: Payment notification sent for billing #%s', billing_id)
    except Exception as e:
        logger.error('SePay Webhook: Failed to send notification for billing #%s - %s', billing_id, e)

    logger.info('SePay Webhook: Completed successfully for billing #%s', billing_id)
    logger.info('='*60)
    
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
