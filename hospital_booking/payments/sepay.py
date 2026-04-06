from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.conf import settings


class SePayService:
    """SePay payment helper for generating QR data and normalizing callback payload."""

    def __init__(self):
        self.bank_code = getattr(settings, 'SEPAY_BANK_CODE', '')
        self.account_number = getattr(settings, 'SEPAY_ACCOUNT_NUMBER', '')
        self.account_name = getattr(settings, 'SEPAY_ACCOUNT_NAME', '')
        self.qr_template = getattr(settings, 'SEPAY_QR_TEMPLATE', 'compact2')

    def build_checkout_data(self, billing):
        """Build checkout data used by QR payment page."""
        transfer_content = f"BILL{billing.id}"
        amount = int(billing.amount)

        query = urlencode(
            {
                'acc': self.account_number,
                'bank': self.bank_code,
                'amount': amount,
                'des': transfer_content,
                'template': self.qr_template,
            }
        )

        qr_image_url = f"https://qr.sepay.vn/img?{query}"

        return {
            'transfer_content': transfer_content,
            'amount': amount,
            'bank_code': self.bank_code,
            'account_number': self.account_number,
            'account_name': self.account_name,
            'qr_image_url': qr_image_url,
        }

    @staticmethod
    def normalize_webhook_payload(payload):
        """Normalize SePay webhook payload so view logic can stay simple."""
        transfer_content = (
            payload.get('transferContent')
            or payload.get('transfer_content')
            or payload.get('description')
            or payload.get('content')
            or payload.get('transactionContent')
            or payload.get('code')
            or ''
        )
        transaction_code = (
            payload.get('id')
            or payload.get('transaction_id')
            or payload.get('referenceCode')
            or payload.get('transactionNo')
            or payload.get('transactionCode')
            or ''
        )

        raw_amount = payload.get('transferAmount')
        if raw_amount is None:
            raw_amount = payload.get('amount')
        if raw_amount is None:
            raw_amount = payload.get('transfer_amount')

        amount_text = str(raw_amount or 0).strip()
        amount_text = amount_text.replace(',', '').replace(' ', '')

        amount = Decimal('0')
        try:
            amount = Decimal(amount_text)
        except (InvalidOperation, TypeError):
            amount = Decimal('0')

        return {
            'transfer_content': str(transfer_content),
            'transaction_code': str(transaction_code),
            'amount': amount,
        }