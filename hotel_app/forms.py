from django import forms
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile, Department, Location, RequestType, Checklist, Complaint, BreakfastVoucher, Review, Guest, Voucher
from django.utils import timezone
from datetime import timedelta



class GuestForm(forms.ModelForm):
    """Enhanced guest registration form with voucher generation"""
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
    
    class Meta:
        model = Guest
        fields = [
            "full_name", "phone", "email", "room_number", 
            "checkin_date", "checkout_date", "breakfast_included",
            "guest_id", "package_type"
        ]
        widgets = {
            'checkin_date': forms.DateInput(attrs={'type': 'date'}),
            'checkout_date': forms.DateInput(attrs={'type': 'date'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guest full name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'guest@example.com'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101, 205A'}),
            'guest_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if left blank'}),
            'package_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Deluxe, Standard, Suite'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default check-in to today, checkout to tomorrow
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['checkin_date'].initial = today
            self.fields['checkout_date'].initial = today + timedelta(days=1)
        
        # Show voucher fields only if breakfast is included
        if self.data.get('breakfast_included') or (self.instance.pk and self.instance.breakfast_included):
            self.fields['create_breakfast_voucher'].widget.attrs['checked'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        checkin_date = cleaned_data.get('checkin_date')
        checkout_date = cleaned_data.get('checkout_date')
        
        if checkin_date and checkout_date:
            if checkout_date <= checkin_date:
                raise forms.ValidationError("Checkout date must be after check-in date.")
            
            # Warn if stay is too long
            if (checkout_date - checkin_date).days > 30:
                raise forms.ValidationError("Stay duration cannot exceed 30 days.")
        
        # Validate phone number format
        phone = cleaned_data.get('phone')
        if phone and not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            raise forms.ValidationError("Please enter a valid phone number.")
        
        return cleaned_data
    
    def save(self, commit=True):
        guest = super().save(commit=commit)
        
        if commit:
            # Create breakfast voucher if requested
            if (self.cleaned_data.get('create_breakfast_voucher') and 
                (guest.breakfast_included or self.cleaned_data.get('breakfast_included'))):
                
                from .utils import generate_voucher_qr_code, generate_voucher_qr_data
                
                # Create voucher
                voucher = Voucher.objects.create(
                    voucher_type='breakfast',
                    guest=guest,
                    guest_name=guest.full_name or 'Guest',
                    room_number=guest.room_number,
                    valid_from=guest.checkin_date,
                    valid_to=guest.checkout_date,
                    quantity=self.cleaned_data.get('voucher_quantity', 1),
                    status='active'
                )
                
                # Generate QR code
                voucher.qr_data = generate_voucher_qr_data(voucher)
                voucher.qr_image = generate_voucher_qr_code(voucher)
                voucher.save()
                
                # TODO: Send WhatsApp if requested
                if self.cleaned_data.get('send_whatsapp'):
                    # This would integrate with WhatsApp Business API
                    voucher.sent_whatsapp = True
                    voucher.whatsapp_sent_at = timezone.now()
                    voucher.save()
        
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
