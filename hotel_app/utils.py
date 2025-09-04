import qrcode
import json
import hashlib
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import base64

def generate_qr_code(data: str, box_size: int = 10, border: int = 5, fill_color: str = "black", back_color: str = "white"):
    """Generate basic QR code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    image_value = buffer.getvalue()

    return ContentFile(image_value, name=f"{data}.png")


def generate_voucher_qr_data(voucher):
    """Generate secure QR data for voucher with validation hash"""
    # Create base data
    qr_data = {
        'voucher_code': voucher.voucher_code,
        'voucher_type': voucher.voucher_type,
        'guest_name': voucher.guest_name,
        'room_number': voucher.room_number,
        'valid_from': voucher.valid_from.isoformat(),
        'valid_to': voucher.valid_to.isoformat(),
        'created_at': voucher.created_at.isoformat(),
        'quantity': voucher.quantity,
    }
    
    # Create verification hash
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    data_string = json.dumps(qr_data, sort_keys=True)
    verification_hash = hashlib.sha256(f"{data_string}{secret_key}".encode()).hexdigest()[:16]
    qr_data['hash'] = verification_hash
    
    return json.dumps(qr_data)


def generate_voucher_qr_code(voucher, size='medium'):
    """Generate QR code specifically for vouchers with enhanced security"""
    
    # Size configurations
    size_configs = {
        'small': {'box_size': 8, 'border': 3},
        'medium': {'box_size': 10, 'border': 4},
        'large': {'box_size': 12, 'border': 5},
    }
    
    config = size_configs.get(size, size_configs['medium'])
    
    # Generate secure QR data
    qr_data = generate_voucher_qr_data(voucher)
    
    # Create QR code with higher error correction for vouchers
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
        box_size=config['box_size'],
        border=config['border'],
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image with hotel branding colors
    img = qr.make_image(
        fill_color="#1a365d",  # Dark blue
        back_color="white"
    )
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_value = buffer.getvalue()
    
    # Create filename with voucher info
    filename = f"voucher_{voucher.voucher_code}_{voucher.voucher_type}.png"
    
    return ContentFile(image_value, name=filename)


def validate_voucher_qr_data(qr_data_string):
    """Validate QR data integrity and return voucher information"""
    try:
        qr_data = json.loads(qr_data_string)
        
        # Check required fields
        required_fields = ['voucher_code', 'voucher_type', 'guest_name', 'hash']
        if not all(field in qr_data for field in required_fields):
            return {'valid': False, 'error': 'Missing required fields'}
        
        # Verify hash
        hash_to_verify = qr_data.pop('hash')
        secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
        data_string = json.dumps(qr_data, sort_keys=True)
        expected_hash = hashlib.sha256(f"{data_string}{secret_key}".encode()).hexdigest()[:16]
        
        if hash_to_verify != expected_hash:
            return {'valid': False, 'error': 'Invalid QR code hash'}
        
        # Check date validity
        try:
            valid_from = datetime.fromisoformat(qr_data['valid_from']).date()
            valid_to = datetime.fromisoformat(qr_data['valid_to']).date()
            today = timezone.now().date()
            
            if not (valid_from <= today <= valid_to):
                return {'valid': False, 'error': 'Voucher expired or not yet valid'}
        except (ValueError, KeyError):
            return {'valid': False, 'error': 'Invalid date format'}
        
        return {'valid': True, 'data': qr_data}
        
    except json.JSONDecodeError:
        return {'valid': False, 'error': 'Invalid QR code format'}
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {str(e)}'}


def create_whatsapp_voucher_message(voucher):
    """Create WhatsApp message content for voucher delivery"""
    message = f"🏨 Hotel Voucher - {voucher.voucher_type.title()}\n\n"
    message += f"Dear {voucher.guest_name},\n\n"
    message += f"Your {voucher.voucher_type} voucher is ready!\n\n"
    message += f"📋 Voucher Details:\n"
    message += f"• Guest: {voucher.guest_name}\n"
    message += f"• Room: {voucher.room_number}\n"
    message += f"• Valid: {voucher.valid_from} to {voucher.valid_to}\n"
    message += f"• Quantity: {voucher.quantity}\n\n"
    message += f"📱 Simply show this QR code at the restaurant/service location.\n\n"
    message += f"Voucher Code: {voucher.voucher_code}\n\n"
    message += f"Thank you for staying with us! 🌟"
    
    return message


def generate_voucher_url(voucher, request=None):
    """Generate URL for voucher details/validation"""
    if request:
        base_url = request.build_absolute_uri('/')
    else:
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000/')
    
    return f"{base_url}api/vouchers/validate/{voucher.voucher_code}/"


def create_voucher_analytics_data(voucher):
    """Create analytics data for voucher"""
    return {
        'voucher_code': voucher.voucher_code,
        'voucher_type': voucher.voucher_type,
        'guest_id': voucher.guest.id if voucher.guest else None,
        'created_date': voucher.created_at.date().isoformat(),
        'valid_period': (voucher.valid_to - voucher.valid_from).days,
        'room_number': voucher.room_number,
        'status': voucher.status,
        'redeemed': voucher.redeemed,
        'whatsapp_sent': voucher.sent_whatsapp,
    }
