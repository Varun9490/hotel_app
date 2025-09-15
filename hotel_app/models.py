import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# ---- Department & Groups ----

class Department(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class UserGroup(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=15, blank=True, null=True)
    title = models.CharField(max_length=120, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, null=True)
    preferences = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username


class UserGroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f'{self.user} -> {self.group}'


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_pk = models.CharField(max_length=100, blank=True, null=True)
    changes = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.model_name} {self.object_pk} by {self.actor}"


# ---- Locations ----

class Building(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Floor(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    floor_number = models.IntegerField()

    class Meta:
        unique_together = ("building", "floor_number")

    def __str__(self):
        return f'{self.building.name} - Floor {self.floor_number}'


class LocationFamily(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class LocationType(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    family = models.ForeignKey(LocationFamily, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(LocationType, on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)
    floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True, null=True)
    room_no = models.CharField(max_length=40, blank=True, null=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("building", "room_no")

    def __str__(self):
        return self.name


# ---- Workflow ----

class RequestFamily(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class WorkFamily(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Workflow(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    step_order = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    role_hint = models.CharField(max_length=120, blank=True, null=True)

    class Meta:
        ordering = ['workflow', 'step_order']
        unique_together = ("workflow", "step_order")

    def __str__(self):
        return f'{self.workflow.name} - {self.step_order}: {self.name}'


class WorkflowTransition(models.Model):
    from_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name='transitions_from')
    to_step = models.ForeignKey(WorkflowStep, on_delete=models.SET_NULL, null=True, related_name='transitions_to')
    condition_expr = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f'{self.from_step} -> {self.to_step}'


# ---- Checklist ----

class Checklist(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    label = models.CharField(max_length=240, blank=True, null=True)
    required = models.BooleanField(default=False)

    def __str__(self):
        return self.label or f'Item {self.pk}'


# ---- Requests ----

class RequestType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    workflow = models.ForeignKey(Workflow, on_delete=models.SET_NULL, null=True, blank=True)
    work_family = models.ForeignKey(WorkFamily, on_delete=models.SET_NULL, null=True, blank=True)
    request_family = models.ForeignKey(RequestFamily, on_delete=models.SET_NULL, null=True, blank=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]
    request_type = models.ForeignKey(RequestType, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    requester_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests_made')
    assignee_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests_assigned')
    priority = models.CharField(max_length=20, blank=True, null=True, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Request #{self.pk}'


class ServiceRequestStep(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('request', 'step')

    def __str__(self):
        return f'{self.request} - {self.step}'


class ServiceRequestChecklist(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE)
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('request', 'item')

    def __str__(self):
        return f'{self.request} - {self.item}'


# ---- Guests ----

class Guest(models.Model):
    full_name = models.CharField(max_length=160, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Enhanced check-in/checkout with time support
    checkin_date = models.DateField(blank=True, null=True)  # Legacy date field
    checkout_date = models.DateField(blank=True, null=True)  # Legacy date field
    checkin_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Check-in Date & Time")
    checkout_datetime = models.DateTimeField(blank=True, null=True, verbose_name="Check-out Date & Time")
    
    # Guest Details QR Code - stored as base64 in database
    details_qr_code = models.TextField(blank=True, null=True, verbose_name="Guest Details QR Code (Base64)")
    details_qr_data = models.TextField(blank=True, null=True, verbose_name="Guest Details QR Data")
    
    breakfast_included = models.BooleanField(default=False)
    guest_id = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)  # Hotel guest ID
    package_type = models.CharField(max_length=50, blank=True, null=True)  # Package or room type
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['guest_id']),
            models.Index(fields=['room_number']),
            models.Index(fields=['checkin_date', 'checkout_date']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Check date fields (legacy)
        if self.checkin_date and self.checkout_date:
            if self.checkout_date <= self.checkin_date:
                raise ValidationError('Checkout date must be after check-in date.')
        
        # Check datetime fields (new)
        if self.checkin_datetime and self.checkout_datetime:
            if self.checkout_datetime <= self.checkin_datetime:
                raise ValidationError('Check-out datetime must be after check-in datetime.')
        
        # Sync date fields with datetime fields
        if self.checkin_datetime and not self.checkin_date:
            self.checkin_date = self.checkin_datetime.date()
        if self.checkout_datetime and not self.checkout_date:
            self.checkout_date = self.checkout_datetime.date()
        
        if self.phone and len(self.phone) < 10:
            raise ValidationError('Phone number must be at least 10 digits.')

    def __str__(self):
        return self.full_name or f'Guest {self.pk}'
    
    def save(self, *args, **kwargs):
        # Generate unique guest ID if not provided
        if not self.guest_id:
            import random
            import string
            while True:
                guest_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Guest.objects.filter(guest_id=guest_id).exists():
                    self.guest_id = guest_id
                    break
        
        # Call clean method for validation
        self.full_clean()
        super().save(*args, **kwargs)
    
    def generate_details_qr_code(self, size='xxlarge'):
        """Generate QR code with all guest details and store as base64"""
        from .utils import generate_guest_details_qr_base64, generate_guest_details_qr_data
        
        try:
            # Generate QR data and base64 image
            self.details_qr_data = generate_guest_details_qr_data(self)
            self.details_qr_code = generate_guest_details_qr_base64(self, size=size)
            self.save(update_fields=['details_qr_data', 'details_qr_code'])
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to generate guest details QR code for {self.guest_id}: {str(e)}')
            return False
    
    def get_details_qr_data_url(self):
        """Get data URL for guest details QR code"""
        if self.details_qr_code:
            return f"data:image/png;base64,{self.details_qr_code}"
        return None
    
    def has_qr_code(self):
        """Check if guest has a QR code"""
        return bool(self.details_qr_code)


class GuestComment(models.Model):
    guest = models.ForeignKey("Guest", on_delete=models.CASCADE, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.CharField(max_length=20)
    source = models.CharField(max_length=20)
    rating = models.PositiveIntegerField(blank=True, null=True)
    comment_text = models.TextField()
    linked_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment {self.pk}'


# ---- Gym ----

class GymMember(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=100, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    plan_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.full_name


class GymVisitor(models.Model):
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class GymVisit(models.Model):
    member = models.ForeignKey(GymMember, on_delete=models.SET_NULL, null=True, blank=True)
    visitor = models.ForeignKey(GymVisitor, on_delete=models.SET_NULL, null=True, blank=True)
    visit_at = models.DateTimeField(blank=True, null=True)
    checked_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=240, blank=True, null=True)

    def __str__(self):
        return f'Visit {self.pk}'


# ---- Booking System ----

class Booking(models.Model):
    """Guest booking/reservation model"""
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    room_number = models.CharField(max_length=20)
    booking_reference = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference']),
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['room_number']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            import random
            import string
            while True:
                ref = 'BK' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Booking.objects.filter(booking_reference=ref).exists():
                    self.booking_reference = ref
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.guest.full_name}"


# ---- Enhanced Voucher System ----

class Voucher(models.Model):
    """Enhanced voucher model with multi-day validation support"""
    VOUCHER_TYPES = [
        ('breakfast', 'Breakfast Voucher'),
        ('gym', 'Gym Voucher'),
        ('spa', 'Spa Voucher'),
        ('restaurant', 'Restaurant Voucher'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('redeemed', 'Fully Redeemed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    voucher_code = models.CharField(max_length=100, unique=True, editable=False)
    voucher_type = models.CharField(max_length=20, choices=VOUCHER_TYPES, default='breakfast')
    
    # Guest & Booking Information
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='vouchers', null=True, blank=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='vouchers', null=True, blank=True)
    guest_name = models.CharField(max_length=100, blank=True, null=True)  # Denormalized for quick access
    room_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Multi-day Validity System
    check_in_date = models.DateField(null=True, blank=True)  # Guest check-in date
    check_out_date = models.DateField(null=True, blank=True)  # Guest check-out date  
    valid_dates = models.JSONField(default=list)  # List of valid dates ["2025-09-07", "2025-09-08"]
    scan_history = models.JSONField(default=list)  # List of scanned dates ["2025-09-07"]
    
    # Legacy fields for backward compatibility
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # QR Code Storage - base64 in database
    qr_image = models.TextField(blank=True, null=True, verbose_name="Voucher QR Code (Base64)")
    qr_data = models.TextField(blank=True, null=True)  # Store QR data for validation
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    redeemed = models.BooleanField(default=False)  # Legacy field - True when fully redeemed
    redeemed_at = models.DateTimeField(null=True, blank=True)  # Last redemption timestamp
    redeemed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='redeemed_vouchers'
    )
    
    # WhatsApp Integration
    sent_whatsapp = models.BooleanField(default=False)
    whatsapp_sent_at = models.DateTimeField(blank=True, null=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional Information
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_vouchers'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['voucher_code']),
            models.Index(fields=['status']),
            models.Index(fields=['guest']),
            models.Index(fields=['check_in_date', 'check_out_date']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def save(self, *args, **kwargs):
        # Generate unique voucher code if not provided
        if not self.voucher_code:
            while True:
                code = str(uuid.uuid4()).replace('-', '').upper()[:12]
                if not Voucher.objects.filter(voucher_code=code).exists():
                    self.voucher_code = code
                    break
        
        # Auto-populate guest information from booking
        if self.booking and not self.guest:
            self.guest = self.booking.guest
            self.room_number = self.booking.room_number
            self.check_in_date = self.booking.check_in.date()
            self.check_out_date = self.booking.check_out.date()
        
        # Auto-populate guest_name from guest if available
        if self.guest and not self.guest_name:
            self.guest_name = self.guest.full_name or 'Guest'
        
        # Auto-generate valid_dates if not provided but check-in/out dates exist
        if not self.valid_dates and self.check_in_date and self.check_out_date:
            from datetime import timedelta
            current_date = self.check_in_date + timedelta(days=1)  # Start from day after check-in
            dates = []
            while current_date <= self.check_out_date:
                dates.append(current_date.isoformat())
                current_date += timedelta(days=1)
            self.valid_dates = dates
        
        # Set legacy fields for backward compatibility
        if not self.valid_from and self.check_in_date:
            self.valid_from = self.check_in_date
        if not self.valid_to and self.check_out_date:
            self.valid_to = self.check_out_date
        
        # Validate dates
        if self.check_in_date and self.check_out_date and self.check_out_date <= self.check_in_date:
            from django.core.exceptions import ValidationError
            raise ValidationError('Check-out date must be after check-in date.')
        
        super().save(*args, **kwargs)

    def is_valid_today(self):
        """Check if voucher is valid for redemption today (your exact requirement)"""
        today = timezone.now().date().isoformat()
        return (
            self.status == 'active' and
            today in self.valid_dates and 
            today not in self.scan_history
        )
    
    def is_expired(self):
        """Check if voucher is expired (after check-out)"""
        if self.check_out_date:
            return timezone.now().date() > self.check_out_date
        if self.valid_to:
            return timezone.now().date() > self.valid_to
        return False
    
    def mark_scanned_today(self, scanned_by_user=None):
        """Mark voucher as scanned for today (your exact requirement)"""
        today = timezone.now().date().isoformat()
        if today not in self.scan_history:
            self.scan_history.append(today)
            
            # Check if all valid dates are now scanned (fully redeemed)
            if set(self.scan_history) >= set(self.valid_dates):
                self.redeemed = True
                self.status = 'redeemed'
                self.redeemed_at = timezone.now()
                self.redeemed_by = scanned_by_user
            
            self.save()
    
    def get_remaining_valid_dates(self):
        """Get list of remaining valid dates that haven't been scanned"""
        return [date for date in self.valid_dates if date not in self.scan_history]
    
    def get_scan_status_for_date(self, date_str):
        """Get scan status for a specific date"""
        if date_str not in self.valid_dates:
            return 'invalid_date'
        if date_str in self.scan_history:
            return 'already_scanned'
        return 'available'
    
    def can_be_redeemed_today(self):
        """Check if voucher can be redeemed today (prevents double redemption)"""
        return self.is_valid_today() and not self.is_expired()
    
    # Legacy method for backward compatibility
    def is_valid(self):
        """Legacy method - check basic validity"""
        if self.valid_from and self.valid_to:
            today = timezone.now().date()
            return (
                self.status == 'active' and
                not self.redeemed and
                self.valid_from <= today <= self.valid_to
            )
        return self.is_valid_today()
    
    def __str__(self):
        return f'{self.voucher_type.title()} Voucher {self.voucher_code} - {self.guest_name}'
    
    def generate_qr_code(self, size='xxlarge'):
        """Generate QR code for voucher and store as base64 - now using larger size for better camera scanning"""
        from .utils import generate_voucher_qr_base64, generate_voucher_qr_data
        
        try:
            # Generate QR data and base64 image with larger default size
            self.qr_data = generate_voucher_qr_data(self)
            self.qr_image = generate_voucher_qr_base64(self, size=size)
            self.save(update_fields=['qr_data', 'qr_image'])
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to generate voucher QR code for {self.voucher_code}: {str(e)}')
            return False
    
    def get_qr_data_url(self):
        """Get data URL for voucher QR code"""
        if self.qr_image:
            return f"data:image/png;base64,{self.qr_image}"
        return None
    
    def has_qr_code(self):
        """Check if voucher has a QR code"""
        return bool(self.qr_image)


class VoucherScan(models.Model):
    """Track all voucher scan attempts for audit and analytics"""
    SCAN_RESULTS = [
        ('success', 'Successful Redemption'),
        ('already_redeemed', 'Already Redeemed'),
        ('expired', 'Expired'),
        ('invalid', 'Invalid Voucher'),
        ('wrong_date', 'Wrong Date'),
        ('error', 'System Error'),
    ]
    
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='scans')
    scanned_at = models.DateTimeField(auto_now_add=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='voucher_scans'
    )
    scan_result = models.CharField(max_length=20, choices=SCAN_RESULTS)
    redemption_successful = models.BooleanField(default=False)
    scan_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    scan_source = models.CharField(max_length=50, default='web')  # web, mobile, tablet
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-scanned_at']
        indexes = [
            models.Index(fields=['voucher', 'scanned_at']),
            models.Index(fields=['scanned_at']),
            models.Index(fields=['scan_result']),
        ]

    def __str__(self):
        return f'Scan {self.id} - {self.voucher.voucher_code} ({self.scan_result})'


# Legacy models for backward compatibility (will be deprecated)
class BreakfastVoucher(models.Model):
    """Legacy model - use Voucher instead"""
    code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    room_no = models.CharField(max_length=20, blank=True, null=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    qr_image = models.ImageField(upload_to="vouchers/", blank=True, null=True)
    qty = models.PositiveIntegerField(default=1)
    valid_from = models.DateField(blank=True, null=True)
    valid_to = models.DateField(blank=True, null=True)
    redeemed_on = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True, choices=[
        ("active", "Active"),
        ("redeemed", "Redeemed"),
        ("expired", "Expired"),
    ], default="active")
    sent_whatsapp = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)

    class Meta:
        verbose_name = 'Legacy Breakfast Voucher'
        verbose_name_plural = 'Legacy Breakfast Vouchers'
        ordering = ['-created_at']

    def is_valid(self):
        today = timezone.now().date()
        return (self.valid_from and self.valid_to and 
                self.valid_from <= today <= self.valid_to and 
                self.status == 'active' and
                (self.redeemed_on != today))
    
    def __str__(self):
        return f'Legacy Voucher {self.code}'

class BreakfastVoucherScan(models.Model):
    """Legacy scan model - use VoucherScan instead"""
    voucher = models.ForeignKey(BreakfastVoucher, on_delete=models.CASCADE, related_name="legacy_scans")
    scanned_at = models.DateTimeField(auto_now_add=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="legacy_voucher_scans"
    )
    source = models.CharField(max_length=50, default="web")

    class Meta:
        verbose_name = 'Legacy Breakfast Voucher Scan'
        verbose_name_plural = 'Legacy Breakfast Voucher Scans'
        ordering = ['-scanned_at']

    def __str__(self):
        return f"Legacy Scan {self.id} for {self.voucher.code}"



# ---- Complaints & Reviews ----

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, blank=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject


class Review(models.Model):
    guest = models.ForeignKey("Guest", on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.guest} - {self.rating} stars"


# --- Proxy models for admin-only screens ---

class MasterUser(User):
    class Meta:
        proxy = True
        verbose_name = 'Master User'
        verbose_name_plural = 'Master Users'


class MasterLocation(Location):
    class Meta:
        proxy = True
        verbose_name = 'Master Location'
        verbose_name_plural = 'Master Locations'