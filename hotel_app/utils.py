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
        'check_in_date': voucher.check_in_date.isoformat() if voucher.check_in_date else None,
        'check_out_date': voucher.check_out_date.isoformat() if voucher.check_out_date else None,
        'valid_dates': voucher.valid_dates,
        'created_at': voucher.created_at.isoformat(),
        'quantity': voucher.quantity,
    }
    
    # Create verification hash
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    data_string = json.dumps(qr_data, sort_keys=True)
    verification_hash = hashlib.sha256(f"{data_string}{secret_key}".encode()).hexdigest()[:16]
    qr_data['hash'] = verification_hash
    
    return json.dumps(qr_data)


def generate_voucher_qr_code(voucher, size='large'):
    """Generate QR code specifically for vouchers with enhanced security and optimized scanning"""
    
    # Size configurations - larger pixels for better camera scanning
    size_configs = {
        'small': {'box_size': 12, 'border': 4},
        'medium': {'box_size': 16, 'border': 5},
        'large': {'box_size': 20, 'border': 6},
        'xlarge': {'box_size': 25, 'border': 7},
    }
    
    config = size_configs.get(size, size_configs['large'])
    
    # Generate secure QR data
    qr_data = generate_voucher_qr_data(voucher)
    
    # Create QR code with medium error correction for vouchers
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction for balance
        box_size=config['box_size'],
        border=config['border'],
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image with high contrast for better scanning
    img = qr.make_image(
        fill_color="#000000",  # Pure black for better contrast
        back_color="#FFFFFF"   # Pure white background
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
        
        # Check date validity (check if any valid dates are still in the future or today)
        try:
            today = timezone.now().date().isoformat()
            valid_dates = qr_data.get('valid_dates', [])
            
            if valid_dates:
                # Check if any valid date is today or in the future
                if not any(date >= today for date in valid_dates):
                    return {'valid': False, 'error': 'All voucher dates have passed'}
            else:
                # Fallback to legacy date validation
                if qr_data.get('check_in_date') and qr_data.get('check_out_date'):
                    check_out = datetime.fromisoformat(qr_data['check_out_date']).date()
                    if check_out < timezone.now().date():
                        return {'valid': False, 'error': 'Voucher expired - past check-out date'}
        except (ValueError, KeyError) as e:
            return {'valid': False, 'error': f'Invalid date format: {str(e)}'}
        
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
        'valid_period': (voucher.check_out_date - voucher.check_in_date).days if voucher.check_out_date and voucher.check_in_date else 0,
        'room_number': voucher.room_number,
        'status': voucher.status,
        'redeemed': voucher.redeemed,
        'whatsapp_sent': voucher.sent_whatsapp,
        'scan_count': len(voucher.scan_history),
        'valid_dates_count': len(voucher.valid_dates),
        'remaining_dates': len(voucher.get_remaining_valid_dates()) if hasattr(voucher, 'get_remaining_valid_dates') else 0,
    }


def generate_guest_details_qr_data(guest):
    """Generate comprehensive QR data with all guest details"""
    qr_data = {
        'type': 'guest_details',
        'guest_id': guest.guest_id,
        'full_name': guest.full_name,
        'phone': guest.phone,
        'email': guest.email,
        'room_number': guest.room_number,
        'package_type': guest.package_type,
        'breakfast_included': guest.breakfast_included,
        'created_at': guest.created_at.isoformat() if guest.created_at else None,
    }
    
    # Add datetime fields if available
    if guest.checkin_datetime:
        qr_data.update({
            'checkin_datetime': guest.checkin_datetime.isoformat(),
            'checkin_date': guest.checkin_datetime.strftime('%Y-%m-%d'),
            'checkin_time': guest.checkin_datetime.strftime('%H:%M'),
        })
    elif guest.checkin_date:
        qr_data['checkin_date'] = guest.checkin_date.isoformat()
    
    if guest.checkout_datetime:
        qr_data.update({
            'checkout_datetime': guest.checkout_datetime.isoformat(),
            'checkout_date': guest.checkout_datetime.strftime('%Y-%m-%d'),
            'checkout_time': guest.checkout_datetime.strftime('%H:%M'),
        })
    elif guest.checkout_date:
        qr_data['checkout_date'] = guest.checkout_date.isoformat()
    
    # Calculate stay duration
    if guest.checkin_datetime and guest.checkout_datetime:
        duration = guest.checkout_datetime - guest.checkin_datetime
        qr_data['stay_duration_hours'] = round(duration.total_seconds() / 3600, 1)
        qr_data['stay_duration_days'] = duration.days
    
    # Add verification hash for security
    secret_key = getattr(settings, 'SECRET_KEY', 'default-secret')
    data_string = json.dumps(qr_data, sort_keys=True)
    verification_hash = hashlib.sha256(f"{data_string}{secret_key}".encode()).hexdigest()[:16]
    qr_data['verification_hash'] = verification_hash
    
    return json.dumps(qr_data, indent=2)


def generate_guest_details_qr_code(guest, size='xlarge'):
    """Generate QR code with all guest details - optimized for camera scanning"""
    
    # Size configurations for guest details (much larger for better camera scanning)
    size_configs = {
        'medium': {'box_size': 15, 'border': 4},
        'large': {'box_size': 20, 'border': 5},
        'xlarge': {'box_size': 25, 'border': 6},  # Much larger pixels for easy scanning
        'xxlarge': {'box_size': 30, 'border': 8},  # Extra large for difficult cameras
    }
    
    config = size_configs.get(size, size_configs['xlarge'])
    
    # Generate comprehensive QR data
    qr_data = generate_guest_details_qr_data(guest)
    
    # Create QR code with medium error correction (balance between size and reliability)
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction for better scanning
        box_size=config['box_size'],
        border=config['border'],
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image with high contrast colors for better scanning
    img = qr.make_image(
        fill_color="#000000",  # Pure black for better contrast
        back_color="#FFFFFF"   # Pure white background
    )
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_value = buffer.getvalue()
    
    # Create filename with guest info
    filename = f"guest_{guest.guest_id}_{guest.full_name.replace(' ', '_') if guest.full_name else 'details'}.png"
    
    return ContentFile(image_value, name=filename)
    """Auto-generate voucher when guest checks in with breakfast included"""
    if not guest.breakfast_included:
        return None
        
    try:
        from .models import Voucher
        
        # Check if voucher already exists
        existing_voucher = Voucher.objects.filter(
            guest=guest, 
            voucher_type='breakfast'
        ).first()
        
        if existing_voucher:
            return existing_voucher
        
        # Create new voucher
        voucher = Voucher.objects.create(
            voucher_type='breakfast',
            guest=guest,
            guest_name=guest.full_name or 'Guest',
            room_number=guest.room_number,
            check_in_date=guest.checkin_date,
            check_out_date=guest.checkout_date,
            quantity=1,
            status='active'
        )
        
        # Generate QR code
        voucher.qr_data = generate_voucher_qr_data(voucher)
        voucher.qr_image = generate_voucher_qr_code(voucher)
        voucher.save()
        
        return voucher
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to auto-generate voucher for guest {guest.id}: {str(e)}', exc_info=True)
        return None
