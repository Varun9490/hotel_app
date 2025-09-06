from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from hotel_app.models import (
    Department, Location, RequestType, Checklist,
    Complaint, BreakfastVoucher, Review, Guest
)
from .forms import (
    UserForm, DepartmentForm, GroupForm, LocationForm,
    RequestTypeForm, ChecklistForm, ComplaintForm,
    BreakfastVoucherForm, ReviewForm
)


# ---- Helpers ----
def is_superuser(user):
    return user.is_superuser


# ---- Dashboard Home ----
@login_required
def dashboard_main(request):
    total_users = User.objects.count()
    total_departments = Department.objects.count()
    total_locations = Location.objects.count()
    active_complaints = Complaint.objects.filter(status="pending").count()
    resolved_complaints = Complaint.objects.filter(status="resolved").count()
    vouchers_issued = BreakfastVoucher.objects.count()
    vouchers_redeemed = BreakfastVoucher.objects.filter(status="redeemed").count()
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


# ---- Users ----
@login_required
def dashboard_users(request):
    users = User.objects.all().select_related("userprofile__department")
    departments = Department.objects.all()
    groups = Group.objects.all()
    return render(request, "dashboard/users.html", {
        "users": users,
        "departments": departments,
        "groups": groups,
    })


@login_required
@user_passes_test(is_superuser)
def user_create(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:users")


@login_required
@user_passes_test(is_superuser)
def user_update(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
    return redirect("dashboard:users")


@login_required
@user_passes_test(is_superuser)
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.delete()
    return redirect("dashboard:users")


# ---- Departments ----
@login_required
def dashboard_departments(request):
    departments = Department.objects.all().annotate(user_count=Count("userprofile"))
    form = DepartmentForm()
    return render(request, "dashboard/departments.html", {
        "departments": departments,
        "form": form,
    })


@login_required
@user_passes_test(is_superuser)
def department_create(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:departments")


@login_required
@user_passes_test(is_superuser)
def department_update(request, dept_id):
    department = get_object_or_404(Department, pk=dept_id)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
    return redirect("dashboard:departments")


@login_required
@user_passes_test(is_superuser)
def department_delete(request, dept_id):
    department = get_object_or_404(Department, pk=dept_id)
    if request.method == "POST":
        department.delete()
    return redirect("dashboard:departments")


# ---- Groups ----
@login_required
def dashboard_groups(request):
    groups = Group.objects.all().annotate(user_count=Count("user"))
    form = GroupForm()
    return render(request, "dashboard/groups.html", {
        "groups": groups,
        "form": form,
    })


@login_required
@user_passes_test(is_superuser)
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:groups")


@login_required
@user_passes_test(is_superuser)
def group_update(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
    return redirect("dashboard:groups")


@login_required
@user_passes_test(is_superuser)
def group_delete(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == "POST":
        group.delete()
    return redirect("dashboard:groups")


# ---- Locations ----
@login_required
def dashboard_locations(request):
    locations = Location.objects.all().select_related("building", "floor", "type")
    form = LocationForm()
    return render(request, "dashboard/locations.html", {
        "locations": locations,
        "form": form,
    })


@login_required
@user_passes_test(is_superuser)
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:locations")


@login_required
@user_passes_test(is_superuser)
def location_update(request, loc_id):
    location = get_object_or_404(Location, pk=loc_id)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
    return redirect("dashboard:locations")


@login_required
@user_passes_test(is_superuser)
def location_delete(request, loc_id):
    location = get_object_or_404(Location, pk=loc_id)
    if request.method == "POST":
        location.delete()
    return redirect("dashboard:locations")


# ---- Request Types ----
@login_required
def dashboard_request_types(request):
    request_types = RequestType.objects.all()
    form = RequestTypeForm()
    return render(request, "dashboard/request_types.html", {
        "request_types": request_types,
        "form": form,
    })


@login_required
@user_passes_test(is_superuser)
def request_type_create(request):
    if request.method == "POST":
        form = RequestTypeForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:request_types")


@login_required
@user_passes_test(is_superuser)
def request_type_update(request, rt_id):
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        form = RequestTypeForm(request.POST, instance=request_type)
        if form.is_valid():
            form.save()
    return redirect("dashboard:request_types")


@login_required
@user_passes_test(is_superuser)
def request_type_delete(request, rt_id):
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        request_type.delete()
    return redirect("dashboard:request_types")


# ---- Checklists ----
@login_required
def dashboard_checklists(request):
    checklists = Checklist.objects.all()
    form = ChecklistForm()
    return render(request, "dashboard/checklists.html", {
        "checklists": checklists,
        "form": form,
    })


@login_required
@user_passes_test(is_superuser)
def checklist_create(request):
    if request.method == "POST":
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:checklists")


@login_required
@user_passes_test(is_superuser)
def checklist_update(request, cl_id):
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        form = ChecklistForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
    return redirect("dashboard:checklists")


@login_required
@user_passes_test(is_superuser)
def checklist_delete(request, cl_id):
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        checklist.delete()
    return redirect("dashboard:checklists")


# ---- Complaints ----
@login_required
def complaints(request):
    complaints_list = Complaint.objects.all()
    form = ComplaintForm()
    return render(request, "dashboard/complaints.html", {
        "complaints": complaints_list,
        "form": form,
        "users": User.objects.all(),
        "guests": Guest.objects.all(),
    })


@login_required
@user_passes_test(is_superuser)
def complaint_create(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:complaints")


@login_required
@user_passes_test(is_superuser)
def complaint_update(request, complaint_id):
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
    return redirect("dashboard:complaints")


@login_required
@user_passes_test(is_superuser)
def complaint_delete(request, complaint_id):
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        complaint.delete()
    return redirect("dashboard:complaints")


# ---- Breakfast Vouchers ----
@login_required
def breakfast_vouchers(request):
    vouchers_list = BreakfastVoucher.objects.all()
    form = BreakfastVoucherForm()
    return render(request, "dashboard/breakfast_vouchers.html", {
        "vouchers": vouchers_list,
        "form": form,
        "guests": Guest.objects.all(),
        "locations": Location.objects.all(),
    })


@login_required
@user_passes_test(is_superuser)
def voucher_create(request):
    if request.method == "POST":
        form = BreakfastVoucherForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:breakfast_vouchers")


@login_required
@user_passes_test(is_superuser)
def voucher_update(request, voucher_id):
    voucher = get_object_or_404(BreakfastVoucher, pk=voucher_id)
    if request.method == "POST":
        form = BreakfastVoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
    return redirect("dashboard:breakfast_vouchers")


@login_required
@user_passes_test(is_superuser)
def voucher_delete(request, voucher_id):
    voucher = get_object_or_404(BreakfastVoucher, pk=voucher_id)
    if request.method == "POST":
        voucher.delete()
    return redirect("dashboard:breakfast_vouchers")


# ---- Reviews ----
@login_required
def reviews(request):
    reviews_list = Review.objects.all()
    form = ReviewForm()
    return render(request, "dashboard/reviews.html", {
        "reviews": reviews_list,
        "form": form,
        "guests": Guest.objects.all(),
    })


@login_required
@user_passes_test(is_superuser)
def review_create(request):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:reviews")


@login_required
@user_passes_test(is_superuser)
def review_update(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
    return redirect("dashboard:reviews")


@login_required
@user_passes_test(is_superuser)
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        review.delete()
    return redirect("dashboard:reviews")


# ---- New Voucher System Dashboard Views ----

@login_required
def voucher_analytics(request):
    """Voucher analytics dashboard with actual data"""
    import json
    from django.utils import timezone
    from django.db.models import Count
    from hotel_app.models import Voucher, VoucherScan
    
    today = timezone.now().date()
    
    # Calculate analytics data
    total_vouchers = Voucher.objects.count()
    active_vouchers = Voucher.objects.filter(status='active').count()
    redeemed_vouchers = Voucher.objects.filter(status='redeemed').count()
    expired_vouchers = Voucher.objects.filter(status='expired').count()
    redeemed_today = VoucherScan.objects.filter(
        scanned_at__date=today,
        redemption_successful=True
    ).count()
    
    # Vouchers by type
    vouchers_by_type = dict(
        Voucher.objects.values('voucher_type').annotate(
            count=Count('id')
        ).values_list('voucher_type', 'count')
    )
    
    # Recent vouchers
    recent_vouchers = Voucher.objects.select_related('guest').order_by('-created_at')[:20]
    
    # Recent scans
    recent_scans = VoucherScan.objects.select_related(
        'voucher', 'voucher__guest', 'scanned_by'
    ).order_by('-scanned_at')[:10]
    
    # Peak redemption hours (simplified - just count by hour)
    # Use raw SQL to extract hour since Extract might not be available
    peak_hours_data = []
    try:
        # Try using TruncHour which is more widely available
        from django.db.models import TruncHour
        peak_hours_qs = VoucherScan.objects.filter(
            redemption_successful=True
        ).annotate(
            hour_truncated=TruncHour('scanned_at')
        ).values('hour_truncated').annotate(
            count=Count('id')
        ).order_by('hour_truncated')
        
        # Convert to hour format
        for item in peak_hours_qs:
            if item['hour_truncated']:
                hour = item['hour_truncated'].hour
                peak_hours_data.append({'hour': hour, 'count': item['count']})
    except ImportError:
        # Fallback: use raw SQL if TruncHour is not available
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT HOUR(scanned_at) as hour, COUNT(*) as count
                FROM hotel_app_voucherscan 
                WHERE redemption_successful = 1
                GROUP BY HOUR(scanned_at)
                ORDER BY hour
            """)
            for row in cursor.fetchall():
                peak_hours_data.append({'hour': row[0], 'count': row[1]})
    
    peak_hours = peak_hours_data
    
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


@login_required
def dashboard_guests(request):
    """Guest management dashboard with filters"""
    from hotel_app.models import Guest
    from django.db.models import Q
    from django.utils import timezone
    
    # Get filter parameters
    search = request.GET.get('search', '')
    breakfast_filter = request.GET.get('breakfast_filter', '')
    status_filter = request.GET.get('status_filter', '')
    qr_filter = request.GET.get('qr_filter', '')
    
    # Base queryset
    guests = Guest.objects.all().order_by('-created_at')
    
    # Apply search filter
    if search:
        guests = guests.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(room_number__icontains=search) |
            Q(guest_id__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Apply breakfast filter
    if breakfast_filter == 'yes':
        guests = guests.filter(breakfast_included=True)
    elif breakfast_filter == 'no':
        guests = guests.filter(breakfast_included=False)
    
    # Apply QR filter
    if qr_filter == 'with_qr':
        guests = guests.exclude(details_qr_code='')
    elif qr_filter == 'without_qr':
        guests = guests.filter(details_qr_code='')
    
    # Apply status filter
    if status_filter:
        today = timezone.now().date()
        if status_filter == 'current':
            guests = guests.filter(
                checkin_date__lte=today,
                checkout_date__gte=today
            )
        elif status_filter == 'past':
            guests = guests.filter(checkout_date__lt=today)
        elif status_filter == 'future':
            guests = guests.filter(checkin_date__gt=today)
    
    return render(request, "dashboard/guests.html", {
        "guests": guests,
        "search": search,
        "breakfast_filter": breakfast_filter,
        "status_filter": status_filter,
        "qr_filter": qr_filter,
        "title": "Guest Management"
    })


@login_required
def guest_detail(request, guest_id):
    """Guest detail view with vouchers"""
    from hotel_app.models import Guest
    guest = get_object_or_404(Guest, pk=guest_id)
    vouchers = guest.vouchers.all().order_by('-created_at')
    
    # Calculate stay duration
    stay_duration = None
    if guest.checkin_date and guest.checkout_date:
        duration = guest.checkout_date - guest.checkin_date
        stay_duration = f"{duration.days} days"
    
    return render(request, "dashboard/guest_detail.html", {
        "guest": guest,
        "vouchers": vouchers,
        "stay_duration": stay_duration,
        "title": f"Guest: {guest.full_name}"
    })


@login_required
def dashboard_vouchers(request):
    """Voucher management dashboard"""
    from hotel_app.models import Voucher
    vouchers = Voucher.objects.all().select_related('guest').order_by('-created_at')
    
    # Calculate status counts
    total_vouchers = vouchers.count()
    active_vouchers = vouchers.filter(status='active').count()
    redeemed_vouchers = vouchers.filter(status='redeemed').count()
    expired_vouchers = vouchers.filter(status='expired').count()
    
    return render(request, "dashboard/vouchers.html", {
        "vouchers": vouchers,
        "total_vouchers": total_vouchers,
        "active_vouchers": active_vouchers,
        "redeemed_vouchers": redeemed_vouchers,
        "expired_vouchers": expired_vouchers,
        "title": "Voucher Management"
    })


@login_required
def voucher_detail(request, voucher_id):
    """Voucher detail view with scan history"""
    from hotel_app.models import Voucher
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    scans = voucher.scans.all().order_by('-scanned_at')
    return render(request, "dashboard/voucher_detail.html", {
        "voucher": voucher,
        "scans": scans,
        "title": f"Voucher: {voucher.voucher_code}"
    })


# ---- Missing Dashboard Views ----

@login_required
def dashboard_request_types(request):
    """Request types management"""
    from hotel_app.models import RequestType
    request_types = RequestType.objects.all()
    from hotel_app.forms import RequestTypeForm
    form = RequestTypeForm()
    return render(request, "dashboard/request_types.html", {
        "request_types": request_types,
        "form": form,
    })


@login_required
def dashboard_checklists(request):
    """Checklists management"""
    from hotel_app.models import Checklist
    checklists = Checklist.objects.all()
    from hotel_app.forms import ChecklistForm
    form = ChecklistForm()
    return render(request, "dashboard/checklists.html", {
        "checklists": checklists,
        "form": form,
    })


@login_required
def complaints(request):
    """Complaints management"""
    from hotel_app.models import Complaint
    complaints = Complaint.objects.all().order_by('-created_at')
    from hotel_app.forms import ComplaintForm
    form = ComplaintForm()
    return render(request, "dashboard/complaints.html", {
        "complaints": complaints,
        "form": form,
    })


@login_required
def breakfast_vouchers(request):
    """Legacy breakfast vouchers view"""
    from hotel_app.models import BreakfastVoucher
    vouchers = BreakfastVoucher.objects.all().order_by('-created_at')
    return render(request, "dashboard/breakfast_vouchers.html", {
        "vouchers": vouchers,
    })


@login_required
def reviews(request):
    """Reviews management"""
    from hotel_app.models import Review
    reviews = Review.objects.all().order_by('-created_at')
    from hotel_app.forms import ReviewForm
    form = ReviewForm()
    return render(request, "dashboard/reviews.html", {
        "reviews": reviews,
        "form": form,
    })


# ---- CRUD Operations for missing views ----

@login_required
@user_passes_test(is_superuser)
def request_type_create(request):
    if request.method == "POST":
        from hotel_app.forms import RequestTypeForm
        form = RequestTypeForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:request_types")


@login_required
@user_passes_test(is_superuser)
def request_type_update(request, rt_id):
    from hotel_app.models import RequestType
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        from hotel_app.forms import RequestTypeForm
        form = RequestTypeForm(request.POST, instance=request_type)
        if form.is_valid():
            form.save()
    return redirect("dashboard:request_types")


@login_required
@user_passes_test(is_superuser)
def request_type_delete(request, rt_id):
    from hotel_app.models import RequestType
    request_type = get_object_or_404(RequestType, pk=rt_id)
    if request.method == "POST":
        request_type.delete()
    return redirect("dashboard:request_types")


@login_required
@user_passes_test(is_superuser)
def checklist_create(request):
    if request.method == "POST":
        from hotel_app.forms import ChecklistForm
        form = ChecklistForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:checklists")


@login_required
@user_passes_test(is_superuser)
def checklist_update(request, cl_id):
    from hotel_app.models import Checklist
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        from hotel_app.forms import ChecklistForm
        form = ChecklistForm(request.POST, instance=checklist)
        if form.is_valid():
            form.save()
    return redirect("dashboard:checklists")


@login_required
@user_passes_test(is_superuser)
def checklist_delete(request, cl_id):
    from hotel_app.models import Checklist
    checklist = get_object_or_404(Checklist, pk=cl_id)
    if request.method == "POST":
        checklist.delete()
    return redirect("dashboard:checklists")


@login_required
@user_passes_test(is_superuser)
def complaint_create(request):
    if request.method == "POST":
        from hotel_app.forms import ComplaintForm
        form = ComplaintForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:complaints")


@login_required
@user_passes_test(is_superuser)
def complaint_update(request, complaint_id):
    from hotel_app.models import Complaint
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        from hotel_app.forms import ComplaintForm
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
    return redirect("dashboard:complaints")


@login_required
@user_passes_test(is_superuser)
def complaint_delete(request, complaint_id):
    from hotel_app.models import Complaint
    complaint = get_object_or_404(Complaint, pk=complaint_id)
    if request.method == "POST":
        complaint.delete()
    return redirect("dashboard:complaints")


@login_required
@user_passes_test(is_superuser)
def voucher_create(request):
    if request.method == "POST":
        from hotel_app.forms import VoucherForm
        form = VoucherForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:vouchers")


@login_required
@user_passes_test(is_superuser)
def voucher_update(request, voucher_id):
    from hotel_app.models import Voucher
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == "POST":
        from hotel_app.forms import VoucherForm
        form = VoucherForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
    return redirect("dashboard:vouchers")


@login_required
@user_passes_test(is_superuser)
def voucher_delete(request, voucher_id):
    from hotel_app.models import Voucher
    voucher = get_object_or_404(Voucher, pk=voucher_id)
    if request.method == "POST":
        voucher.delete()
    return redirect("dashboard:vouchers")


@login_required
@user_passes_test(is_superuser)
def review_create(request):
    if request.method == "POST":
        from hotel_app.forms import ReviewForm
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect("dashboard:reviews")


@login_required
@user_passes_test(is_superuser)
def review_update(request, review_id):
    from hotel_app.models import Review
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        from hotel_app.forms import ReviewForm
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
    return redirect("dashboard:reviews")


@login_required
@user_passes_test(is_superuser)
def review_delete(request, review_id):
    from hotel_app.models import Review
    review = get_object_or_404(Review, pk=review_id)
    if request.method == "POST":
        review.delete()
    return redirect("dashboard:reviews")


# ---- Guest QR Codes Dashboard ----

@login_required
def guest_qr_codes(request):
    """Display all guest QR codes in a grid layout"""
    from hotel_app.models import Guest
    from django.db.models import Q
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    filter_status = request.GET.get('filter', 'all')
    
    # Base queryset
    guests = Guest.objects.all().order_by('-created_at')
    
    # Apply search filter
    if search:
        guests = guests.filter(
            Q(full_name__icontains=search) |
            Q(guest_id__icontains=search) |
            Q(room_number__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Apply status filter
    if filter_status == 'with_qr':
        guests = guests.exclude(details_qr_code='')
    elif filter_status == 'without_qr':
        guests = guests.filter(details_qr_code='')
    elif filter_status == 'current':
        from django.utils import timezone
        today = timezone.now().date()
        guests = guests.filter(
            checkin_date__lte=today,
            checkout_date__gte=today
        )
    
    # Calculate statistics
    total_guests = Guest.objects.count()
    guests_with_qr = Guest.objects.exclude(details_qr_code='').count()
    guests_without_qr = total_guests - guests_with_qr
    
    context = {
        'guests': guests,
        'search': search,
        'filter_status': filter_status,
        'total_guests': total_guests,
        'guests_with_qr': guests_with_qr,
        'guests_without_qr': guests_without_qr,
        'title': 'Guest QR Codes'
    }
    
    return render(request, "dashboard/guest_qr_codes.html", context)


@login_required
def regenerate_guest_qr(request, guest_id):
    """Regenerate QR code for a specific guest"""
    from hotel_app.models import Guest
    guest = get_object_or_404(Guest, pk=guest_id)
    
    if request.method == "POST":
        try:
            # Get size from form or default to xlarge
            size = request.POST.get('qr_size', 'xlarge')
            success = guest.generate_details_qr_code(size=size)
            
            if success:
                messages.success(request, f"QR code regenerated successfully for {guest.full_name}!")
            else:
                messages.error(request, f"Failed to regenerate QR code for {guest.full_name}. Please try again.")
        except Exception as e:
            messages.error(request, f"Error regenerating QR code: {str(e)}")
    
    return redirect('dashboard:guest_qr_codes')
