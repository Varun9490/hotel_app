import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncHour
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import JsonResponse
from django.db import connection

# Import all models from hotel_app
from hotel_app.models import (
    Department, Location, RequestType, Checklist,
    Complaint, BreakfastVoucher, Review, Guest,
    Voucher, VoucherScan
)

# Import all forms from the local forms.py
from .forms import (
    UserForm, DepartmentForm, GroupForm, LocationForm,
    RequestTypeForm, ChecklistForm, ComplaintForm,
    BreakfastVoucherForm, ReviewForm, VoucherForm
)

# Import local utils and services
from .utils import user_in_group
from hotel_app.whatsapp_service import WhatsAppService


# ---- Constants ----
ADMINS_GROUP = 'Admins'
STAFF_GROUP = 'Staff'
USERS_GROUP = 'Users'


# ---- Helper Functions ----
def is_admin(user):
    """Check if a user is an admin or superuser."""
    return user.is_superuser or user_in_group(user, ADMINS_GROUP)

def is_staff(user):
    """Check if a user is staff, admin, or superuser."""
    return (user.is_superuser or
            user_in_group(user, ADMINS_GROUP) or
            user_in_group(user, STAFF_GROUP))

@login_required
@user_passes_test(is_staff)
def dashboard(request):
    """Main dashboard view."""
    # Get system status
    system_statuses = [
        {'name': 'Camera Health', 'value': '98%', 'color': 'green-500'},
        {'name': 'Import/Export Activity', 'value': 'Active', 'color': 'gray-900'},
        {'name': 'Billing Status', 'value': 'Current', 'color': 'green-500'},
    ]

    # Get checklist data
    checklists = [
        {'name': 'Housekeeping', 'completed': 18, 'total': 20, 'status_color': 'green', 'percentage': 90},
        {'name': 'Maintenance', 'completed': 12, 'total': 15, 'status_color': 'yellow', 'percentage': 80},
    ]

    # Get WhatsApp campaigns
    whatsapp_campaigns = [
        {'name': 'Welcome Message', 'time': '10:00 AM', 'status_color': 'green-500'},
        {'name': 'Checkout Reminder', 'time': '2:00 PM', 'status_color': 'yellow-400'},
        {'name': 'Feedback Request', 'time': '6:00 PM', 'status_color': 'sky-600'},
    ]

    # Get requests data for chart
    requests_data = {
        'labels': ['Housekeeping', 'Maintenance', 'Concierge', 'F&B', 'IT Support', 'Other'],
        'values': [95, 75, 45, 35, 25, 15]
    }

    # Get feedback data for chart
    feedback_data = {
        'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'positive': [70, 80, 75, 90, 85, 95, 100],
        'neutral': [20, 25, 30, 25, 35, 30, 25],
        'negative': [15, 10, 20, 15, 12, 10, 8]
    }

    context = {
        'system_statuses': system_statuses,
        'checklists': checklists,
        'whatsapp_campaigns': whatsapp_campaigns,
        'requests_data': json.dumps(requests_data),
        'feedback_data': json.dumps(feedback_data),
    }
    
    return render(request, 'dashboard/dashboard.html', context)

def require_permission(group_names):
    """Decorator to require specific group permissions for a view."""
    if not isinstance(group_names, (list, tuple)):
        group_names = [group_names]
    
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser or any(user_in_group(request.user, group) for group in group_names):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("You don't have permission to access this page.")
        return wrapper
    return decorator


# ---- Dashboard Home ----
@login_required
def dashboard_main(request):
    """Main dashboard view with key metrics."""
    total_users = User.objects.count()
    total_departments = Department.objects.count()
    total_locations = Location.objects.count()
    active_complaints = Complaint.objects.filter(status="pending").count()
    resolved_complaints = Complaint.objects.filter(status="resolved").count()
    vouchers_issued = Voucher.objects.count()
    vouchers_redeemed = Voucher.objects.filter(status="redeemed").count()
    average_review_rating = Review.objects.aggregate(Avg("rating"))["rating__avg"] or 0
    complaint_trends = Complaint.objects.values("status").annotate(count=Count("id"))

    context = {
        "total_users": total_users,
        "total_departments": total_departments,
        "total_locations": total_locations,
        "active_complaints": active_complaints,
        "resolved_complaints": resolved_complaints,
        "vouchers_issued": vouchers_issued,
        "vouchers_redeemed": vouchers_redeemed,
        "average_review_rating": f"{average_review_rating:.2f}",
        "complaint_trends": list(complaint_trends),
    }
    return render(request, "dashboard/main.html", context)


from django.contrib.auth.decorators import login_required


@login_required
def dashboard_view(request):
    """Render the dashboard with live metrics for users, departments and open complaints.

    - total_users: count of User objects
    - total_departments: count of Department objects
    - open_complaints: count of Complaint objects with pending/open status
    """
    # Live counts
    try:
        total_users = User.objects.count()
    except Exception:
        total_users = 0

    try:
        total_departments = Department.objects.count()
    except Exception:
        total_departments = 0

    try:
        open_complaints = Complaint.objects.filter(status__in=["pending", "open"]).count()
    except Exception:
        # Fallback to Complaint model count if status field differs
        try:
            open_complaints = Complaint.objects.count()
        except Exception:
            open_complaints = 0

    # Keep other cards as examples/static values for now
    context = {
        'total_users': total_users,
        'total_departments': total_departments,
        'open_complaints': open_complaints,
    }
    return render(request, 'dashboard/dashboard.html', context)

# ---- User Management ----
@require_permission([ADMINS_GROUP])
def dashboard_users(request):
    users = User.objects.all().select_related("userprofile__department")
    departments = Department.objects.all()
    groups = Group.objects.all()
    context = {
        "users": users,
        "departments": departments,
        "groups": groups,
    }
    return render(request, "dashboard/users.html", context)

@require_permission([ADMINS_GROUP])
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
        else:
            messages.error(request, "Please correct the errors below.")
    return redirect("dashboard:users")

@require_permission([ADMINS_GROUP])
def user_update(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
    return redirect("dashboard:users")

@require_permission([ADMINS_GROUP])
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect("dashboard:users")


# ---- Department Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_departments(request):
    departments = Department.objects.all().annotate(user_count=Count("userprofile"))
    form = DepartmentForm()
    context = {
        "departments": departments,
        "form": form,
    }
    return render(request, "dashboard/departments.html", context)

@require_permission([ADMINS_GROUP])
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully.")
    return redirect("dashboard:departments")

@require_permission([ADMINS_GROUP])
def department_update(request, dept_id):
    department = get_object_or_404(Department, pk=dept_id)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
    return redirect("dashboard:departments")

@require_permission([ADMINS_GROUP])
def department_delete(request, dept_id):
    department = get_object_or_404(Department, pk=dept_id)
    if request.method == "POST":
        department.delete()
        messages.success(request, "Department deleted successfully.")
    return redirect("dashboard:departments")


# ---- Group Management ----
@require_permission([ADMINS_GROUP])
def dashboard_groups(request):
    groups = Group.objects.all().annotate(user_count=Count("user"))
    form = GroupForm()
    context = {
        "groups": groups,
        "form": form,
    }
    return render(request, "dashboard/groups.html", context)

@require_permission([ADMINS_GROUP])
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Group created successfully.")
    return redirect("dashboard:groups")

@require_permission([ADMINS_GROUP])
def group_update(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Group updated successfully.")
    return redirect("dashboard:groups")

@require_permission([ADMINS_GROUP])
def group_delete(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == "POST":
        group.delete()
        messages.success(request, "Group deleted successfully.")
    return redirect("dashboard:groups")


# ---- Location Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_locations(request):
    locations = Location.objects.all().select_related("building", "floor", "type")
    form = LocationForm()
    context = {
        "locations": locations,
        "form": form,
    }
    return render(request, "dashboard/locations.html", context)

@require_permission([ADMINS_GROUP])
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Location created successfully.")
    return redirect("dashboard:locations")

@require_permission([ADMINS_GROUP])
def location_update(request, loc_id):
    location = get_object_or_404(Location, pk=loc_id)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, "Location updated successfully.")
    return redirect("dashboard:locations")

@require_permission([ADMINS_GROUP])
def location_delete(request, loc_id):
    location = get_object_or_404(Location, pk=loc_id)
    if request.method == "POST":
        location.delete()
        messages.success(request, "Location deleted successfully.")
    return redirect("dashboard:locations")


# ---- Request Type Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_request_types(request):
    request_types = RequestType.objects.all()
    form = RequestTypeForm()
    context = {
        "request_types": request_types,
        "form": form,
    }
    return render(request, "dashboard/request_types.html", context)

@require_permission([ADMINS_GROUP])
def request_type_create(request):
    if request.method == "POST":
        form = RequestTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Request Type created successfully.")
    return redirect("dashboard:request_types")

@require_permission([ADMINS_GROUP])
def request_type_update(request, rt_id):
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        form = RequestTypeForm(request.POST, instance=request_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Request Type updated successfully.")
    return redirect("dashboard:request_types")

@require_permission([ADMINS_GROUP])
def request_type_delete(request, rt_id):
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        request_type.delete()
        messages.success(request, "Request Type deleted successfully.")
    return redirect("dashboard:request_types")


# ---- Checklist Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_checklists(request):
    checklists = Checklist.objects.all()
    form = ChecklistForm()
    context = {
        "checklists": checklists,
        "form": form,
    }
    return render(request, "dashboard/checklists.html", context)

@require_permission([ADMINS_GROUP])
def checklist_create(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Checklist created successfully.")
    return redirect("dashboard:checklists")

@require_permission([ADMINS_GROUP])
def checklist_update(request, cl_id):
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        form = ChecklistForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
            messages.success(request, "Checklist updated successfully.")
    return redirect("dashboard:checklists")

@require_permission([ADMINS_GROUP])
def checklist_delete(request, cl_id):
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        checklist.delete()
        messages.success(request, "Checklist deleted successfully.")
    return redirect("dashboard:checklists")


# ---- Complaint Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def complaints(request):
    complaints_list = Complaint.objects.all().order_by('-created_at')
    form = ComplaintForm()
    context = {
        "complaints": complaints_list,
        "form": form,
        "users": User.objects.all(),
        "guests": Guest.objects.all(),
    }
    return render(request, "dashboard/complaints.html", context)

@require_permission([ADMINS_GROUP])
def complaint_create(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Complaint logged successfully.")
    return redirect("dashboard:complaints")

@require_permission([ADMINS_GROUP])
def complaint_update(request, complaint_id):
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, "Complaint updated successfully.")
    return redirect("dashboard:complaints")

@require_permission([ADMINS_GROUP])
def complaint_delete(request, complaint_id):
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        complaint.delete()
        messages.success(request, "Complaint deleted successfully.")
    return redirect("dashboard:complaints")


# ---- Legacy Breakfast Voucher Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def breakfast_vouchers(request):
    vouchers_list = BreakfastVoucher.objects.all().order_by('-created_at')
    form = BreakfastVoucherForm()
    context = {
        "vouchers": vouchers_list,
        "form": form,
        "guests": Guest.objects.all(),
        "locations": Location.objects.all(),
    }
    return render(request, "dashboard/breakfast_vouchers.html", context)


# ---- Review Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def reviews(request):
    reviews_list = Review.objects.all().order_by('-created_at')
    form = ReviewForm()
    context = {
        "reviews": reviews_list,
        "form": form,
        "guests": Guest.objects.all(),
    }
    return render(request, "dashboard/reviews.html", context)

@require_permission([ADMINS_GROUP])
def review_create(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Review submitted successfully.")
    return redirect("dashboard:reviews")

@require_permission([ADMINS_GROUP])
def review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
    return redirect("dashboard:reviews")

@require_permission([ADMINS_GROUP])
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        review.delete()
        messages.success(request, "Review deleted successfully.")
    return redirect("dashboard:reviews")


# ---- New Voucher System: Analytics ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def voucher_analytics(request):
    """Voucher analytics dashboard with actual data."""
    today = timezone.now().date()
    
    total_vouchers = Voucher.objects.count()
    active_vouchers = Voucher.objects.filter(status='active').count()
    redeemed_vouchers = Voucher.objects.filter(status='redeemed').count()
    expired_vouchers = Voucher.objects.filter(status='expired').count()
    redeemed_today = VoucherScan.objects.filter(scanned_at__date=today, redemption_successful=True).count()
    
    vouchers_by_type = dict(
        Voucher.objects.values('voucher_type').annotate(count=Count('id')).values_list('voucher_type', 'count')
    )
    
    recent_vouchers = Voucher.objects.select_related('guest').order_by('-created_at')[:20]
    recent_scans = VoucherScan.objects.select_related('voucher', 'voucher__guest', 'scanned_by').order_by('-scanned_at')[:10]
    
    # Peak redemption hours using Django ORM's TruncHour
    peak_hours_data = list(
        VoucherScan.objects.filter(redemption_successful=True)
        .annotate(hour_truncated=TruncHour('scanned_at'))
        .values('hour_truncated')
        .annotate(count=Count('id'))
        .order_by('hour_truncated')
    )
    # Reformat for chart
    peak_hours = [{'hour': item['hour_truncated'].hour, 'count': item['count']} for item in peak_hours_data if item['hour_truncated']]

    analytics_data = {
        'total_vouchers': total_vouchers,
        'active_vouchers': active_vouchers,
        'redeemed_vouchers': redeemed_vouchers,
        'expired_vouchers': expired_vouchers,
        'redeemed_today': redeemed_today,
        'vouchers_by_type': vouchers_by_type,
        'peak_hours': peak_hours,
    }
    
    context = {
        'analytics': analytics_data,
        'analytics_json': json.dumps(analytics_data),
        'recent_vouchers': recent_vouchers,
        'recent_scans': recent_scans,
    }
    return render(request, "dashboard/voucher_analytics.html", context)


# ---- New Voucher System: Guest Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_guests(request):
    """Guest management dashboard with filters."""
    search = request.GET.get('search', '')
    breakfast_filter = request.GET.get('breakfast_filter', '')
    status_filter = request.GET.get('status_filter', '')
    qr_filter = request.GET.get('qr_filter', '')
    
    guests = Guest.objects.all().order_by('-created_at')
    
    if search:
        guests = guests.filter(
            Q(full_name__icontains=search) | Q(email__icontains=search) |
            Q(room_number__icontains=search) | Q(guest_id__icontains=search) |
            Q(phone__icontains=search)
        )
    if breakfast_filter == 'yes':
        guests = guests.filter(breakfast_included=True)
    elif breakfast_filter == 'no':
        guests = guests.filter(breakfast_included=False)
    if qr_filter == 'with_qr':
        guests = guests.exclude(details_qr_code='')
    elif qr_filter == 'without_qr':
        guests = guests.filter(details_qr_code='')
    if status_filter:
        today = timezone.now().date()
        if status_filter == 'current':
            guests = guests.filter(checkin_date__lte=today, checkout_date__gte=today)
        elif status_filter == 'past':
            guests = guests.filter(checkout_date__lt=today)
        elif status_filter == 'future':
            guests = guests.filter(checkin_date__gt=today)
    
    context = {
        "guests": guests,
        "search": search,
        "breakfast_filter": breakfast_filter,
        "status_filter": status_filter,
        "qr_filter": qr_filter,
        "title": "Guest Management"
    }
    return render(request, "dashboard/guests.html", context)

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def guest_detail(request, guest_id):
    """Guest detail view with vouchers and stay information."""
    guest = get_object_or_404(Guest, pk=guest_id)
    vouchers = guest.vouchers.all().order_by('-created_at')
    
    stay_duration = "N/A"
    if guest.checkin_date and guest.checkout_date:
        duration = guest.checkout_date - guest.checkin_date
        stay_duration = f"{duration.days} days"
    
    context = {
        "guest": guest,
        "vouchers": vouchers,
        "stay_duration": stay_duration,
        "title": f"Guest: {guest.full_name}"
    }
    return render(request, "dashboard/guest_detail.html", context)


# ---- New Voucher System: Voucher Management ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def dashboard_vouchers(request):
    """Voucher management dashboard."""
    vouchers = Voucher.objects.all().select_related('guest').order_by('-created_at')
    
    for voucher in vouchers:
        if not voucher.qr_image:
            voucher.generate_qr_code(size='xxlarge')
    
    context = {
        "vouchers": vouchers,
        "total_vouchers": vouchers.count(),
        "active_vouchers": vouchers.filter(status='active').count(),
        "redeemed_vouchers": vouchers.filter(status='redeemed').count(),
        "expired_vouchers": vouchers.filter(status='expired').count(),
        "title": "Voucher Management"
    }
    return render(request, "dashboard/vouchers.html", context)

@require_permission([ADMINS_GROUP])
def voucher_create(request):
    if request.method == "POST":
        form = VoucherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Voucher created successfully.")
    return redirect("dashboard:vouchers")

@require_permission([ADMINS_GROUP])
def voucher_update(request, voucher_id):
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == "POST":
        form = VoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            messages.success(request, "Voucher updated successfully.")
    return redirect("dashboard:vouchers")

@require_permission([ADMINS_GROUP])
def voucher_delete(request, voucher_id):
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == "POST":
        voucher.delete()
        messages.success(request, "Voucher deleted successfully.")
    return redirect("dashboard:vouchers")

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def voucher_detail(request, voucher_id):
    """Voucher detail view with scan history."""
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    scans = voucher.scans.all().order_by('-scanned_at')
    
    if not voucher.qr_image:
        if voucher.generate_qr_code(size='xxlarge'):
            messages.success(request, 'QR code generated successfully!')
        else:
            messages.error(request, 'Failed to generate QR code.')
    
    context = {
        "voucher": voucher,
        "scans": scans,
        "title": f"Voucher: {voucher.voucher_code}"
    }
    return render(request, "dashboard/voucher_detail.html", context)

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def regenerate_voucher_qr(request, voucher_id):
    """Regenerate QR code for a specific voucher."""
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == 'POST':
        qr_size = request.POST.get('qr_size', 'xxlarge')
        if voucher.generate_qr_code(size=qr_size):
            messages.success(request, f'QR code regenerated with size: {qr_size}!')
        else:
            messages.error(request, 'Failed to regenerate QR code.')
    return redirect('dashboard:voucher_detail', voucher_id=voucher.id)

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def share_voucher_whatsapp(request, voucher_id):
    """Share voucher via WhatsApp API."""
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == 'POST':
        if not voucher.guest or not voucher.guest.phone:
            return JsonResponse({'success': False, 'error': 'Guest phone number is not available.'})
        try:
            whatsapp_service = WhatsAppService()
            result = whatsapp_service.send_voucher_message(voucher)
            if result.get('success'):
                return JsonResponse({'success': True, 'message': 'Voucher shared via WhatsApp!'})
            else:
                return JsonResponse({'success': False, 'error': 'WhatsApp API unavailable.', 'fallback': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Service error: {str(e)}', 'fallback': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


# ---- Guest QR Codes Dashboard ----
@require_permission([ADMINS_GROUP, STAFF_GROUP])
def guest_qr_codes(request):
    """Display all guest QR codes in a grid layout with filters."""
    search = request.GET.get('search', '')
    filter_status = request.GET.get('filter', 'all')
    
    guests = Guest.objects.all().order_by('-created_at')
    
    if search:
        guests = guests.filter(
            Q(full_name__icontains=search) | Q(guest_id__icontains=search) |
            Q(room_number__icontains=search)
        )
    if filter_status == 'with_qr':
        guests = guests.exclude(details_qr_code='')
    elif filter_status == 'without_qr':
        guests = guests.filter(details_qr_code='')
    elif filter_status == 'current':
        today = timezone.now().date()
        guests = guests.filter(checkin_date__lte=today, checkout_date__gte=today)
    
    total_guests = Guest.objects.count()
    context = {
        'guests': guests,
        'search': search,
        'filter_status': filter_status,
        'total_guests': total_guests,
        'guests_with_qr': Guest.objects.exclude(Q(details_qr_code='') | Q(details_qr_code__isnull=True)).count(),
        'guests_without_qr': Guest.objects.filter(Q(details_qr_code='') | Q(details_qr_code__isnull=True)).count(),
        'title': 'Guest QR Codes'
    }
    return render(request, "dashboard/guest_qr_codes.html", context)

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def regenerate_guest_qr(request, guest_id):
    """Regenerate QR code for a specific guest."""
    guest = get_object_or_404(Guest, pk=guest_id)
    if request.method == 'POST':
        qr_size = request.POST.get('qr_size', 'xlarge')
        if guest.generate_details_qr_code(size=qr_size):
            messages.success(request, f'Guest QR code regenerated with size: {qr_size}!')
        else:
            messages.error(request, 'Failed to regenerate guest QR code.')
    return redirect('dashboard:guest_detail', guest_id=guest.id)

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def share_guest_qr_whatsapp(request, guest_id):
    """Share guest QR code via WhatsApp API."""
    guest = get_object_or_404(Guest, pk=guest_id)
    if request.method == 'POST':
        if not guest.phone:
            return JsonResponse({'success': False, 'error': 'Guest phone number not available.'})
        try:
            whatsapp_service = WhatsAppService()
            result = whatsapp_service.send_guest_qr_message(guest)
            if result.get('success'):
                return JsonResponse({'success': True, 'message': 'Guest QR code shared via WhatsApp!'})
            else:
                return JsonResponse({'success': False, 'error': 'WhatsApp API unavailable.', 'fallback': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Service error: {str(e)}', 'fallback': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@require_permission([ADMINS_GROUP, STAFF_GROUP])
def get_guest_whatsapp_message(request, guest_id):
    """Get a pre-formatted WhatsApp message template for a guest."""
    guest = get_object_or_404(Guest, pk=guest_id)
    message = (
        f"Hello {guest.full_name},\n\n"
        f"Welcome! Here is your personal QR code for accessing hotel services.\n\n"
        f"Guest ID: {guest.guest_id}\n"
        f"Room: {guest.room_number}"
    )
    return JsonResponse({
        'success': True,
        'message': message,
        'guest_name': guest.full_name,
        'guest_phone': guest.phone
    })


# ---- Tailwind Test ----
@login_required
def tailwind_test(request):
    """View for testing Tailwind CSS functionality."""
    return render(request, "dashboard/tailwind_test.html")
