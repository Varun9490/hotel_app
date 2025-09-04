"""
WhatsApp Integration Service for Hotel Voucher System
Mock implementation - replace with actual WhatsApp Business API
"""

import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import Voucher
from .utils import create_whatsapp_voucher_message, generate_voucher_url

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Mock WhatsApp Business API integration"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'WHATSAPP_API_URL', 'https://graph.facebook.com/v17.0')
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', 'mock_token')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', 'mock_phone_id')
    
    def send_voucher(self, voucher, recipient_phone):
        """Send voucher via WhatsApp"""
        try:
            # In production, replace with actual WhatsApp API call
            message = create_whatsapp_voucher_message(voucher)
            
            # Mock API call - replace with actual implementation
            response = self._mock_send_message(recipient_phone, message, voucher)
            
            if response.get('success'):
                voucher.sent_whatsapp = True
                voucher.whatsapp_sent_at = timezone.now()
                voucher.whatsapp_message_id = response.get('message_id')
                voucher.save()
                
                logger.info(f"WhatsApp voucher sent successfully: {voucher.voucher_code}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp voucher: {response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"WhatsApp service error: {str(e)}")
            return False
    
    def _mock_send_message(self, phone, message, voucher):
        """Mock WhatsApp API call - replace with actual implementation"""
        # Simulate API response
        import uuid
        return {
            'success': True,
            'message_id': str(uuid.uuid4()),
            'phone': phone,
            'status': 'sent'
        }
    
    def _actual_send_message(self, phone, message, voucher):
        """Actual WhatsApp Business API implementation"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        # Format phone number
        if not phone.startswith('+'):
            phone = '+' + phone.replace('-', '').replace(' ', '')
        
        # Prepare message payload
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": "voucher_delivery",
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": voucher.guest_name},
                            {"type": "text", "text": voucher.voucher_type},
                            {"type": "text", "text": voucher.voucher_code}
                        ]
                    }
                ]
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global service instance
whatsapp_service = WhatsAppService()