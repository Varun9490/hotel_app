from django import forms
from django.contrib.auth.models import User, Group
from hotel_app.models import UserProfile, Department, Location, RequestType, Checklist, Complaint, BreakfastVoucher, Review

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
