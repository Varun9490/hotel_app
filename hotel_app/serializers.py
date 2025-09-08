from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, UserGroup, UserProfile, UserGroupMembership,
    Building, Floor, LocationFamily, LocationType, Location,
    RequestFamily, WorkFamily, Workflow, WorkflowStep, WorkflowTransition,
    Checklist, ChecklistItem, RequestType, ServiceRequest, 
    ServiceRequestStep, ServiceRequestChecklist,
    Guest, GuestComment, Booking,  # Added Booking
    GymMember, GymVisitor, GymVisit,
    BreakfastVoucher, BreakfastVoucherScan,
    Voucher, VoucherScan,  # Enhanced voucher models
    Complaint, Review
)

# -------------------
# Core User & Groups
# -------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_active', 'date_joined'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get("username"),
            email=validated_data.get("email"),
            password=validated_data.get("password"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'


class UserGroupMembershipSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    group_details = UserGroupSerializer(source='group', read_only=True)

    class Meta:
        model = UserGroupMembership
        fields = '__all__'


# -------------------
# Locations
# -------------------

class LocationSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    floor_number = serializers.IntegerField(source='floor.floor_number', read_only=True)

    class Meta:
        model = Location
        fields = '__all__'


# -------------------
# Service Requests
# -------------------

class ServiceRequestSerializer(serializers.ModelSerializer):
    request_type_name = serializers.CharField(source='request_type.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    requester_name = serializers.CharField(source='requester_user.get_full_name', read_only=True)
    assignee_name = serializers.CharField(source='assignee_user.get_full_name', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = '__all__'


# -------------------
# Guest & Vouchers
# -------------------

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'


# -------------------
# Booking System
# -------------------

class BookingSerializer(serializers.ModelSerializer):
    guest_details = GuestSerializer(source='guest', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['booking_reference', 'created_at', 'updated_at']


# -------------------
# Enhanced Voucher System
# -------------------

class VoucherSerializer(serializers.ModelSerializer):
    guest_details = GuestSerializer(source='guest', read_only=True)
    booking_details = BookingSerializer(source='booking', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    is_valid_today = serializers.SerializerMethodField()
    can_redeem_today = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    scan_count = serializers.SerializerMethodField()
    qr_image_url = serializers.SerializerMethodField()
    remaining_valid_dates = serializers.SerializerMethodField()
    total_valid_dates = serializers.SerializerMethodField()
    redemption_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = '__all__'
        read_only_fields = ['voucher_code', 'qr_data', 'scan_history', 'created_at', 'updated_at']

    def get_is_valid_today(self, obj):
        return obj.is_valid_today()
    
    def get_can_redeem_today(self, obj):
        return obj.can_be_redeemed_today()
    
    def get_days_until_expiry(self, obj):
        from django.utils import timezone
        if obj.check_out_date:
            days = (obj.check_out_date - timezone.now().date()).days
            return max(0, days)
        elif obj.valid_to:
            days = (obj.valid_to - timezone.now().date()).days
            return max(0, days)
        return 0
    
    def get_scan_count(self, obj):
        return obj.scans.count()
    
    def get_qr_image_url(self, obj):
        if obj.qr_image:
            # Return data URL for base64 QR codes
            return f"data:image/png;base64,{obj.qr_image}"
        return None
    
    def get_remaining_valid_dates(self, obj):
        return obj.get_remaining_valid_dates()
    
    def get_total_valid_dates(self, obj):
        return len(obj.valid_dates)
    
    def get_redemption_percentage(self, obj):
        if len(obj.valid_dates) == 0:
            return 0
        return round((len(obj.scan_history) / len(obj.valid_dates)) * 100, 1)


class VoucherScanSerializer(serializers.ModelSerializer):
    voucher_details = VoucherSerializer(source='voucher', read_only=True)
    scanned_by_name = serializers.CharField(source='scanned_by.get_full_name', read_only=True)
    location_name = serializers.CharField(source='scan_location.name', read_only=True)

    class Meta:
        model = VoucherScan
        fields = '__all__'
        read_only_fields = ['scanned_at']


class VoucherValidationSerializer(serializers.Serializer):
    """Serializer for voucher validation requests"""
    voucher_code = serializers.CharField(max_length=100, required=False)
    qr_data = serializers.CharField(required=False)
    scan_location = serializers.CharField(max_length=100, required=False)
    
    def validate(self, data):
        if not data.get('voucher_code') and not data.get('qr_data'):
            raise serializers.ValidationError(
                "Either voucher_code or qr_data must be provided"
            )
        return data


class VoucherValidationResponseSerializer(serializers.Serializer):
    """Serializer for voucher validation responses"""
    valid = serializers.BooleanField()
    message = serializers.CharField()
    voucher_details = VoucherSerializer(required=False)
    scan_result = serializers.CharField(required=False)
    error_code = serializers.CharField(required=False)


class VoucherCreateSerializer(serializers.ModelSerializer):
    """Enhanced serializer for creating new vouchers"""
    generate_qr = serializers.BooleanField(default=True, write_only=True)
    send_whatsapp = serializers.BooleanField(default=False, write_only=True)
    auto_generate_dates = serializers.BooleanField(default=True, write_only=True)
    
    class Meta:
        model = Voucher
        fields = [
            'voucher_type', 'booking', 'guest', 'guest_name', 'room_number',
            'check_in_date', 'check_out_date', 'valid_dates', 'quantity', 
            'location', 'special_instructions', 'generate_qr', 'send_whatsapp',
            'auto_generate_dates'
        ]
    
    def create(self, validated_data):
        generate_qr = validated_data.pop('generate_qr', True)
        send_whatsapp = validated_data.pop('send_whatsapp', False)
        auto_generate_dates = validated_data.pop('auto_generate_dates', True)
        
        # Set created_by from request user
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        
        voucher = super().create(validated_data)
        
        # Generate QR code if requested
        if generate_qr:
            from .utils import generate_voucher_qr_base64, generate_voucher_qr_data
            voucher.qr_data = generate_voucher_qr_data(voucher)
            voucher.qr_image = generate_voucher_qr_base64(voucher)
            voucher.save()
        
        # TODO: Send WhatsApp message if requested
        if send_whatsapp:
            # This would integrate with WhatsApp API
            pass
        
        return voucher


class GuestCreateSerializer(serializers.ModelSerializer):
    """Enhanced guest serializer with voucher creation"""
    create_breakfast_voucher = serializers.BooleanField(default=False, write_only=True)
    voucher_quantity = serializers.IntegerField(default=1, write_only=True)
    
    class Meta:
        model = Guest
        fields = '__all__'
    
    def create(self, validated_data):
        create_voucher = validated_data.pop('create_breakfast_voucher', False)
        voucher_quantity = validated_data.pop('voucher_quantity', 1)
        
        guest = super().create(validated_data)
        
        # Auto-create breakfast voucher if breakfast is included
        if guest.breakfast_included or create_voucher:
            # Import here to avoid circular imports
            from .models import Voucher
            from .utils import generate_voucher_qr_code, generate_voucher_qr_data
            
            # Create voucher directly
            voucher = Voucher.objects.create(
                voucher_type='breakfast',
                guest=guest,
                guest_name=guest.full_name or 'Guest',
                room_number=guest.room_number,
                valid_from=guest.checkin_date,
                valid_to=guest.checkout_date,
                quantity=voucher_quantity,
                status='active'
            )
            
            # Generate QR code
            try:
                voucher.qr_data = generate_voucher_qr_data(voucher)
                voucher.qr_image = generate_voucher_qr_base64(voucher)
                voucher.save()
            except Exception as e:
                # Log error but don't fail guest creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to generate QR code for voucher {voucher.voucher_code}: {str(e)}')
        
        return guest


# -------------------
# Voucher Analytics
# -------------------

class VoucherAnalyticsSerializer(serializers.Serializer):
    """Serializer for voucher analytics data"""
    total_vouchers = serializers.IntegerField()
    active_vouchers = serializers.IntegerField()
    redeemed_vouchers = serializers.IntegerField()
    expired_vouchers = serializers.IntegerField()
    redeemed_today = serializers.IntegerField()
    vouchers_by_type = serializers.DictField()
    peak_redemption_hours = serializers.ListField()
    

class VoucherReportSerializer(serializers.Serializer):
    """Serializer for detailed voucher reports"""
    date_range = serializers.CharField()
    total_issued = serializers.IntegerField()
    total_redeemed = serializers.IntegerField()
    redemption_rate = serializers.FloatField()
    avg_days_to_redemption = serializers.FloatField()
    popular_times = serializers.ListField()
    by_voucher_type = serializers.DictField()
    by_location = serializers.DictField()


# -------------------
# Legacy Support
# -------------------

class BreakfastVoucherSerializer(serializers.ModelSerializer):
    """Legacy breakfast voucher serializer"""
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = BreakfastVoucher
        fields = '__all__'


class BreakfastVoucherScanSerializer(serializers.ModelSerializer):
    """Legacy breakfast voucher scan serializer"""
    class Meta:
        model = BreakfastVoucherScan
        fields = '__all__'


class GuestCommentSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = GuestComment
        fields = '__all__'


# -------------------
# Dashboard Analytics
# -------------------

class DashboardMetricsSerializer(serializers.Serializer):
    complaints_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    vouchers_count = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()


class ComplaintAnalyticsSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class ReviewAnalyticsSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    count = serializers.IntegerField()


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
