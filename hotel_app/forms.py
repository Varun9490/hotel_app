from django import forms
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile, Department, Location, RequestType, Checklist, Complaint, BreakfastVoucher, Review, Guest, Voucher
from django.utils import timezone
from datetime import timedelta



class GuestForm(forms.ModelForm):
    """Enhanced guest registration form with datetime support for check-in/out"""
    # Additional fields for voucher generation
    create_breakfast_voucher = forms.BooleanField(
        required=False,
        initial=True,
        label="Create Breakfast Voucher",
        help_text="Automatically create breakfast voucher if breakfast is included"
    )
    voucher_quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        required=False,
        label="Voucher Quantity",
        help_text="Number of breakfast vouchers to create"
    )
    send_whatsapp = forms.BooleanField(
        required=False,
        initial=False,
        label="Send via WhatsApp",
        help_text="Send voucher to guest via WhatsApp"
    )
    generate_guest_qr = forms.BooleanField(
        required=False,
        initial=True,
        label="Generate Guest Details QR Code",
        help_text="Create QR code with all guest information for easy access"
    )
    qr_code_size = forms.ChoiceField(
        choices=[
            ('large', 'Large (Recommended)'),
            ('xlarge', 'Extra Large (Easy Scanning)'),
            ('xxlarge', 'XXL (Difficult Cameras)'),
            ('medium', 'Medium (Compact)')
        ],
        initial='xlarge',
        required=False,
        label="QR Code Size",
        help_text="Larger sizes are easier to scan with phone cameras"
    )
    
    class Meta:
        model = Guest
        fields = [
            "full_name", "phone", "email", "room_number", 
            "checkin_datetime", "checkout_datetime", "breakfast_included",
            "guest_id", "package_type"
        ]
        widgets = {
            'checkin_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'placeholder': 'Select check-in date and time'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'checkout_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local', 
                    'class': 'form-control',
                    'placeholder': 'Select check-out date and time'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guest full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'guest@example.com'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101, 205A'}),
            'guest_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if left blank'}),
            'package_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Deluxe, Standard, Suite'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default check-in to today at 2 PM, checkout to tomorrow at 11 AM
        if not self.instance.pk:
            from datetime import datetime, time
            today = timezone.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Default check-in: today at 2:00 PM
            default_checkin = timezone.make_aware(
                datetime.combine(today, time(14, 0))  # 2:00 PM
            )
            # Default check-out: tomorrow at 11:00 AM  
            default_checkout = timezone.make_aware(
                datetime.combine(tomorrow, time(11, 0))  # 11:00 AM
            )
            
            self.fields['checkin_datetime'].initial = default_checkin
            self.fields['checkout_datetime'].initial = default_checkout
        
        # Show voucher fields only if breakfast is included
        if self.data.get('breakfast_included') or (self.instance.pk and self.instance.breakfast_included):
            self.fields['create_breakfast_voucher'].widget.attrs['checked'] = True
            
        # Add helpful labels and help text
        self.fields['checkin_datetime'].help_text = "Select the date and time when guest checks in (e.g., 2:00 PM)"
        self.fields['checkout_datetime'].help_text = "Select the date and time when guest checks out (e.g., 11:00 AM)"
        
    def clean(self):
        cleaned_data = super().clean()
        checkin_datetime = cleaned_data.get('checkin_datetime')
        checkout_datetime = cleaned_data.get('checkout_datetime')
        
        if checkin_datetime and checkout_datetime:
            if checkout_datetime <= checkin_datetime:
                raise forms.ValidationError("Check-out datetime must be after check-in datetime.")
            
            # Warn if stay is too long
            if (checkout_datetime.date() - checkin_datetime.date()).days > 30:
                raise forms.ValidationError("Stay duration cannot exceed 30 days.")
            
            # Warn if check-in is too far in the past
            if checkin_datetime.date() < (timezone.now().date() - timedelta(days=7)):
                raise forms.ValidationError("Check-in date cannot be more than 7 days in the past.")
        
        # Validate phone number format (more lenient)
        phone = cleaned_data.get('phone')
        if phone:
            # Remove common formatting characters
            phone_digits = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if phone_digits and not phone_digits.isdigit():
                raise forms.ValidationError("Phone number should contain only digits and common formatting characters (+, -, spaces, parentheses).")
            
            # Check minimum length (more lenient)
            if len(phone_digits) < 7:
                raise forms.ValidationError("Phone number must be at least 7 digits long.")
        
        return cleaned_data
    
    def save(self, commit=True):
        guest = super().save(commit=commit)
        
        if commit:
            # Sync legacy date fields with datetime fields
            if guest.checkin_datetime:
                guest.checkin_date = guest.checkin_datetime.date()
            if guest.checkout_datetime:
                guest.checkout_date = guest.checkout_datetime.date()
            
            # Save again to update the synced fields
            guest.save(update_fields=['checkin_date', 'checkout_date'])
            
            # Create breakfast voucher if requested
            if (self.cleaned_data.get('create_breakfast_voucher') and 
                (guest.breakfast_included or self.cleaned_data.get('breakfast_included'))):
                
                from .utils import generate_voucher_qr_code, generate_voucher_qr_data
                
                # Create voucher with enhanced date handling
                voucher_data = {
                    'voucher_type': 'breakfast',
                    'guest': guest,
                    'guest_name': guest.full_name or 'Guest',
                    'room_number': guest.room_number,
                    'quantity': self.cleaned_data.get('voucher_quantity', 1),
                    'status': 'active'
                }
                
                # Use datetime fields if available, fallback to date fields
                if guest.checkin_datetime and guest.checkout_datetime:
                    voucher_data.update({
                        'check_in_date': guest.checkin_datetime.date(),
                        'check_out_date': guest.checkout_datetime.date(),
                    })
                elif guest.checkin_date and guest.checkout_date:
                    voucher_data.update({
                        'check_in_date': guest.checkin_date,
                        'check_out_date': guest.checkout_date,
                        'valid_from': guest.checkin_date,
                        'valid_to': guest.checkout_date,
                    })
                
                voucher = Voucher.objects.create(**voucher_data)
                
                # Generate QR code
                try:
                    voucher.qr_data = generate_voucher_qr_data(voucher)
                    voucher.qr_image = generate_voucher_qr_code(voucher)
                    voucher.save()
                except Exception as e:
                    # Log error but don't fail guest creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to generate QR code for voucher {voucher.voucher_code}: {str(e)}')
                
                # TODO: Send WhatsApp if requested
                if self.cleaned_data.get('send_whatsapp'):
                    # This would integrate with WhatsApp Business API
                    voucher.sent_whatsapp = True
                    voucher.whatsapp_sent_at = timezone.now()
                    voucher.save(update_fields=['sent_whatsapp', 'whatsapp_sent_at'])
            
            # Generate guest details QR code if requested
            if self.cleaned_data.get('generate_guest_qr', True):
                try:
                    # Get the selected QR code size
                    qr_size = self.cleaned_data.get('qr_code_size', 'xlarge')
                    from .utils import generate_guest_details_qr_code, generate_guest_details_qr_data
                    
                    # Generate QR data and image with specified size
                    guest.details_qr_data = generate_guest_details_qr_data(guest)
                    guest.details_qr_code = generate_guest_details_qr_code(guest, size=qr_size)
                    guest.save(update_fields=['details_qr_data', 'details_qr_code'])
                except Exception as e:
                    # Log error but don't fail guest creation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to generate guest details QR code for {guest.guest_id}: {str(e)}')
        
        return guest


class VoucherForm(forms.ModelForm):
    """Form for creating/editing vouchers"""
    generate_qr = forms.BooleanField(
        required=False,
        initial=True,
        label="Generate QR Code",
        help_text="Automatically generate QR code for this voucher"
    )
    
    class Meta:
        model = Voucher
        fields = [
            'voucher_type', 'guest', 'guest_name', 'room_number',
            'valid_from', 'valid_to', 'quantity', 'location',
            'special_instructions', 'status'
        ]
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_to': forms.DateInput(attrs={'type': 'date'}),
            'special_instructions': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default dates
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['valid_from'].initial = today
            self.fields['valid_to'].initial = today + timedelta(days=7)
        
        # If guest is selected, auto-fill guest name and room
        if self.instance.guest:
            self.fields['guest_name'].initial = self.instance.guest.full_name
            self.fields['room_number'].initial = self.instance.guest.room_number
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        if valid_from and valid_to:
            if valid_to <= valid_from:
                raise forms.ValidationError("Valid to date must be after valid from date.")
        
        return cleaned_data
    
    def save(self, commit=True):
        voucher = super().save(commit=commit)
        
        if commit and self.cleaned_data.get('generate_qr'):
            from .utils import generate_voucher_qr_code, generate_voucher_qr_data
            
            # Generate QR code
            voucher.qr_data = generate_voucher_qr_data(voucher)
            voucher.qr_image = generate_voucher_qr_code(voucher)
            voucher.save()
        
        return voucher


class VoucherScanForm(forms.Form):
    """Form for manual voucher scanning/validation"""
    voucher_code = forms.CharField(
        max_length=100,
        label="Voucher Code",
        help_text="Enter the voucher code to validate",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter voucher code',
            'autofocus': True
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Optional notes about this scan'
        }),
        label="Notes"
    )



class UserForm(forms.ModelForm):
    full_name = forms.CharField(max_length=160, required=True)
    phone = forms.CharField(max_length=15, required=False)
    title = forms.CharField(max_length=120, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.userprofile
                self.fields['full_name'].initial = profile.full_name
                self.fields['phone'].initial = profile.phone
                self.fields['title'].initial = profile.title
                self.fields['department'].initial = profile.department
            except UserProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.instance.pk: # Set a default password for new users
            user.set_password('password123') # You should have a more secure way to handle this
        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data['full_name']
            profile.phone = self.cleaned_data['phone']
            profile.title = self.cleaned_data['title']
            profile.department = self.cleaned_data['department']
            profile.save()
        return user

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'description']

class RequestTypeForm(forms.ModelForm):
    class Meta:
        model = RequestType
        fields = ['name', 'description']

class ChecklistForm(forms.ModelForm):
    class Meta:
        model = Checklist
        fields = ['name', 'description']

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['guest', 'subject', 'description', 'status']

class BreakfastVoucherForm(forms.ModelForm):
    class Meta:
        model = BreakfastVoucher
        fields = ['guest', 'room_no', 'location', 'qty', 'valid_from', 'valid_to', 'status']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['guest', 'rating', 'comment']
