"""
WhatsApp Integration Service for Hotel Voucher System
Mock implementation - replace with actual WhatsApp Business API
"""

import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import Voucher
from .utils import generate_voucher_qr_base64

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Mock WhatsApp Business API integration"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'WHATSAPP_API_URL', 'https://graph.facebook.com/v17.0')
        self.access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', 'mock_token')
        self.phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', 'mock_phone_id')
    
    def send_guest_qr(self, guest, recipient_phone=None):
        """Send guest QR code with details via WhatsApp"""
        try:
            # Use guest's phone if no recipient specified
            phone = recipient_phone or guest.phone
            if not phone:
                logger.error(f"No phone number available for guest {guest.guest_id}")
                return False
            
            # Create guest details message
            message = self._create_guest_details_message(guest)
            
            # Send image first if QR code exists
            if guest.details_qr_code:
                image_response = self._send_image_message(phone, guest.details_qr_code, guest)
                if not image_response.get('success'):
                    logger.warning(f"Failed to send QR image to {phone}, sending text only")
            
            # Send text message with details
            text_response = self._send_text_message(phone, message)
            
            if text_response.get('success'):
                logger.info(f"Guest QR details sent successfully to {phone} for guest {guest.guest_id}")
                return True
            else:
                logger.error(f"Failed to send guest QR details: {text_response.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"WhatsApp guest QR service error: {str(e)}")
            return False
    
    def _create_guest_details_message(self, guest):
        """Create formatted guest details message"""
        message = "🏨 Hotel Guest Details\n\n"
        message += f"👤 Guest: {guest.full_name}\n"
        message += f"📱 Phone: {guest.phone or 'Not provided'}\n"
        message += f"🆔 Guest ID: {guest.guest_id}\n"
        message += f"🏠 Room: {guest.room_number or 'Not assigned'}\n"
        
        if guest.checkin_date:
            message += f"📅 Check-in: {guest.checkin_date.strftime('%b %d, %Y')}\n"
        if guest.checkout_date:
            message += f"📅 Check-out: {guest.checkout_date.strftime('%b %d, %Y')}\n"
        
        message += f"🍳 Breakfast: {'Included' if guest.breakfast_included else 'Not Included'}\n\n"
        message += "📱 Please scan the QR code above to access your hotel services.\n\n"
        message += "Thank you for choosing our hotel! 🌟"
        
        return message
    
    def _send_image_message(self, phone, qr_base64_data, guest):
        """Send QR code image via WhatsApp Business API"""
        if not qr_base64_data:
            return {'success': False, 'error': 'No QR image available'}
        
        # Format phone number
        if not phone.startswith('+'):
            phone = '+91' + phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # In production, you would first upload the base64 image to WhatsApp Media API
        # and get a media_id, then send it
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        # For now, return mock success - implement actual media upload in production
        return self._mock_send_image(phone, qr_base64_data, guest)
    
    def _send_text_message(self, phone, message):
        """Send text message via WhatsApp"""
        # Format phone number
        if not phone.startswith('+'):
            phone = '+91' + phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            # In production environment
            if self.access_token != 'mock_token':
                response = requests.post(url, json=payload, headers=headers)
                return response.json()
            else:
                # Mock response for development
                return self._mock_send_text(phone, message)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Public helper to allow sending simple text notifications from other modules
    def send_text(self, phone, message):
        """Public method: send a text message (wrapped around internal implementation). Returns True/False."""
        try:
            resp = self._send_text_message(phone, message)
            return resp.get('success', False)
        except Exception:
            return False
    
    def _mock_send_image(self, phone, qr_base64_data, guest):
        """Mock image sending for development"""
        import uuid
        logger.info(f"MOCK: Sending QR image for guest {guest.guest_id} to {phone} (Base64 data: {len(qr_base64_data) if qr_base64_data else 0} chars)")
        return {
            'success': True,
            'message_id': str(uuid.uuid4()),
            'type': 'image',
            'phone': phone
        }
    
    def _mock_send_text(self, phone, message):
        """Mock text sending for development"""
        import uuid
        logger.info(f"MOCK: Sending text message to {phone}: {message[:50]}...")
        return {
            'success': True,
            'message_id': str(uuid.uuid4()),
            'type': 'text',
            'phone': phone
        }
    
    def send_voucher(self, voucher, recipient_phone):
        try:
            # Generate QR code for voucher
            qr_base64 = generate_voucher_qr_base64(voucher, size="medium")

            # Format voucher details text (optional, alongside QR image)
            message = (
                "🎟️ *Hotel Voucher*\n\n"
                f"👤 Guest: {voucher.guest_name}\n"
                f"🏠 Room: {voucher.room_number or 'Not assigned'}\n"
                f"🍳 Type: {voucher.voucher_type}\n"
                f"🔑 Code: {voucher.voucher_code}\n\n"
                f"📅 Issued: {voucher.issued_at.strftime('%b %d, %Y') if voucher.issued_at else 'N/A'}\n"
                f"⏳ Valid until: {voucher.valid_until.strftime('%b %d, %Y') if voucher.valid_until else 'Not specified'}\n\n"
                "📱 Scan the QR code above to validate your voucher."
            )

            # First send QR image
            image_response = self._send_image_message(recipient_phone, qr_base64, voucher)
            if not image_response.get("success"):
                logger.warning(f"Failed to send voucher QR image to {recipient_phone}, sending text only")

            # Then send text
            text_response = self._send_text_message(recipient_phone, message)

            if text_response.get("success"):
                voucher.sent_whatsapp = True
                voucher.whatsapp_sent_at = timezone.now()
                voucher.whatsapp_message_id = text_response.get("message_id")
                voucher.save()

                logger.info(f"WhatsApp voucher QR sent successfully: {voucher.voucher_code}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp voucher text: {text_response.get('error')}")
                return False

        except Exception as e:
            logger.error(f"WhatsApp voucher QR service error: {str(e)}")
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