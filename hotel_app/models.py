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
    checkin_date = models.DateField(blank=True, null=True)
    checkout_date = models.DateField(blank=True, null=True)
    breakfast_included = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name or f'Guest {self.pk}'


class GuestComment(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
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


# ---- Breakfast Vouchers ----

class BreakfastVoucher(models.Model):
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
    ])
    sent_whatsapp = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        today = timezone.now().date()
        return (self.valid_from and self.valid_to and self.valid_from <= today <= self.valid_to) and (self.redeemed_on != today)

    def __str__(self):
        return f'Voucher {self.code} - {self.guest.full_name if self.guest else "No Guest"}'


class BreakfastVoucherScan(models.Model):
    voucher = models.ForeignKey(BreakfastVoucher, on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=20, blank=True, null=True)
    scanned_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Scan {self.pk}'


class BreakfastVoucherScan(models.Model):
    voucher = models.ForeignKey(BreakfastVoucher, on_delete=models.CASCADE, related_name="scans")
    scanned_at = models.DateTimeField(auto_now_add=True)
    scanned_by = models.ForeignKey(  # ✅ FIXED HERE
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="voucher_scans"
    )
    source = models.CharField(max_length=50, default="web")

    def __str__(self):
        return f"Scan {self.id} for {self.voucher.voucher_code}"

class Voucher(models.Model):
    guest_name = models.CharField(max_length=100)
    voucher_code = models.CharField(
        max_length=100, unique=True, default=uuid.uuid4
    )
    expiry_date = models.DateField()
    redeemed = models.BooleanField(default=False)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.CharField(max_length=100, null=True, blank=True)  # staff name or ID

    def __str__(self):
        return f"{self.guest_name} - {self.voucher_code}"

    def is_valid(self):
        """Check if the voucher is still valid."""
        return not self.redeemed and self.expiry_date >= timezone.now().date()

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class Review(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

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
