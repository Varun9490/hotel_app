from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.db.models import Count, Avg
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
