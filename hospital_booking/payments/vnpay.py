import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings


class VNPayService:
    """VNPay payment integration service"""
    
    def __init__(self):
        self.vnp_TmnCode = settings.VNPAY_TMN_CODE
        self.vnp_HashSecret = settings.VNPAY_HASH_SECRET_KEY
        self.vnp_Url = settings.VNPAY_PAYMENT_URL
        self.vnp_ReturnUrl = settings.VNPAY_RETURN_URL
    
    def create_payment_url(self, order_id, amount, order_desc, ip_addr, bank_code=None):
        """Create VNPay payment URL"""
        vnp_Params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.vnp_TmnCode,
            'vnp_Amount': int(amount) * 100,  # VNPay requires amount in VND * 100
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': order_id,
            'vnp_OrderInfo': order_desc,
            'vnp_OrderType': 'billpayment',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.vnp_ReturnUrl,
            'vnp_IpAddr': ip_addr,
            'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
        }
        
        if bank_code:
            vnp_Params['vnp_BankCode'] = bank_code
        
        # Sort params
        sorted_params = sorted(vnp_Params.items())
        
        # Build query string
        query_string = urllib.parse.urlencode(sorted_params)
        
        # Create hash
        hash_value = self._hmac_sha512(self.vnp_HashSecret, query_string)
        
        # Build final URL
        payment_url = f"{self.vnp_Url}?{query_string}&vnp_SecureHash={hash_value}"
        
        return payment_url
    
    def verify_response(self, response_data):
        """Verify VNPay response"""
        vnp_SecureHash = response_data.get('vnp_SecureHash', '')
        
        # Remove hash params for verification
        params_to_verify = {k: v for k, v in response_data.items() 
                           if k not in ['vnp_SecureHash', 'vnp_SecureHashType']}
        
        sorted_params = sorted(params_to_verify.items())
        query_string = urllib.parse.urlencode(sorted_params)
        
        calculated_hash = self._hmac_sha512(self.vnp_HashSecret, query_string)
        
        return vnp_SecureHash == calculated_hash
    
    def _hmac_sha512(self, key, data):
        """Generate HMAC SHA512 hash"""
        byte_key = key.encode('utf-8')
        byte_data = data.encode('utf-8')
        return hmac.new(byte_key, byte_data, hashlib.sha512).hexdigest()
