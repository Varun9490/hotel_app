import json
import csv
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LogoutView
from django.db.models import Count
from django.views.generic import TemplateView
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from hotel_app.models import (
    User, Department, UserGroup, UserGroupMembership,
    Location, ServiceRequest, Voucher, GuestComment, Guest,
    Notification  # Add Notification model
)
from hotel_app.serializers import (
    UserSerializer, DepartmentSerializer, UserGroupSerializer,
    UserGroupMembershipSerializer, LocationSerializer,
    ServiceRequestSerializer, GuestCommentSerializer
)
from hotel_app.utils import generate_qr_code, user_in_group, group_required, admin_required, create_notification  # Add create_notification
from .forms import GuestForm
from .models import Guest
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


# ------------------- Constants -------------------
ADMINS_GROUP = 'Admins'
USERS_GROUP = 'Users'
STAFF_GROUP = 'Staff'


# ------------------- Auth -------------------
class LoginView(TokenObtainPairView):
    """JWT login view"""
    permission_classes = [AllowAny]


class CustomLogoutView(LogoutView):
    """Allow GET request for logout (by redirecting to POST logic)."""
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    is_admin = (
        request.user.is_authenticated
        and (request.user.is_superuser or user_in_group(request.user, ADMINS_GROUP))
    )
    return render(request, "home.html", {"is_admin": is_admin})


# ------------------- Helper Functions -------------------
def user_in_group(user, group_name):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())


# ------------------- Admin Mixins -------------------
class AdminOnlyView(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to Admin users only."""
    def test_func(self):
        return user_in_group(self.request.user, ADMINS_GROUP)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict access to Staff and Admin users only."""
    def test_func(self):
        return (user_in_group(self.request.user, ADMINS_GROUP) or 
                user_in_group(self.request.user, STAFF_GROUP))


# ------------------- API ViewSets -------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]


class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [IsAuthenticated]


class UserGroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = UserGroupMembership.objects.all()
    serializer_class = UserGroupMembershipSerializer
    permission_classes = [IsAuthenticated]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    permission_classes = [IsAuthenticated]


class GuestCommentViewSet(viewsets.ModelViewSet):
    queryset = GuestComment.objects.all()
    serializer_class = GuestCommentSerializer
    permission_classes = [IsAuthenticated]


# ------------------- Dashboard APIs -------------------
class DashboardOverview(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = {
            "complaints": ServiceRequest.objects.count(),
            "reviews": GuestComment.objects.count(),
            "vouchers": Voucher.objects.count(),
        }
        return Response(data)


class DashboardComplaints(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total = ServiceRequest.objects.count()
        open_requests = ServiceRequest.objects.filter(status="open").count()
        closed_requests = ServiceRequest.objects.filter(status="closed").count()
        return Response({"total": total, "open": open_requests, "closed": closed_requests})


class DashboardReviews(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total = GuestComment.objects.count()
        return Response({"total": total})


# ------------------- Voucher Management -------------------
from django.shortcuts import render
from .models import Voucher

def breakfast_vouchers(request):
    vouchers = Voucher.objects.all()
    return render(request, "dashboard/", {"vouchers": vouchers})


def issue_voucher(request, guest_id):
    """Generate voucher + QR for a guest at check-in"""
    # Check if user has permission to issue vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to issue vouchers.")
    
    guest = get_object_or_404(Guest, id=guest_id)

    if not guest.breakfast_included:
        return render(request, "dashboard/issue_voucher.html", {"error": "Guest does not have breakfast included."})

    voucher, created = Voucher.objects.get_or_create(
        guest_name=guest.full_name,
        expiry_date=guest.checkout_date,
    )
    
    # Set the issued_by field to the current user
    voucher.issued_by = request.user

    if created or not voucher.qr_code:
        # Generate QR code with larger size for better visibility
        qr_data = f"Voucher: {voucher.voucher_code}\nGuest: {voucher.guest_name}"
        voucher.qr_image = generate_qr_code(qr_data, size='xxlarge')
    
    voucher.save()
    
    # Create a notification for the user who issued the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Issued",
        message=f"Voucher for {voucher.guest_name} has been issued successfully.",
        notification_type="voucher",
        related_object=voucher
    )

    return render(request, "dashboard/voucher_detail.html", {"voucher": voucher})


@require_http_methods(["POST"])
def scan_voucher(request, code=None):
    """Validate & redeem QR voucher via POST request."""
    # Check if user has permission to scan vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    code = code or request.POST.get("voucher_code")
    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({"status": "invalid", "message": "Voucher not found"}, status=404)

    if not voucher.is_valid():
        return JsonResponse({"status": "expired", "message": "Voucher expired or already redeemed"})

    voucher.redeemed = True
    voucher.save()
    
    # Create a notification for the user who scanned the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Scanned",
        message=f"Voucher for {voucher.guest_name} has been scanned successfully.",
        notification_type="voucher",
        related_object=voucher
    )
    
    # Create a notification for the user who issued the voucher (if different)
    if voucher.issued_by and voucher.issued_by != request.user:
        create_notification(
            recipient=voucher.issued_by,
            title="Voucher Redeemed",
            message=f"Voucher for {voucher.guest_name} has been redeemed.",
            notification_type="voucher",
            related_object=voucher
        )

    return JsonResponse({
        "status": "success",
        "guest": voucher.guest_name,
        "scan_id": voucher.id,
    })


def validate_voucher(request):
    """Validate & redeem QR voucher via GET request."""
    # Check if user has permission to validate vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"status": "error", "message": "Code missing"}, status=400)

    try:
        voucher = Voucher.objects.get(voucher_code=code)
    except Voucher.DoesNotExist:
        return JsonResponse({"status": "invalid", "message": "Voucher not found"}, status=404)

    if not voucher.is_valid():
        return JsonResponse({"status": "expired", "message": "Voucher expired or already redeemed"}, status=400)

    # Redeem the voucher
    voucher.redeemed = True
    voucher.save()
    
    # Create a notification for the user who validated the voucher
    create_notification(
        recipient=request.user,
        title="Voucher Validated",
        message=f"Voucher for {voucher.guest_name} has been validated successfully.",
        notification_type="voucher",
        related_object=voucher
    )
    
    # Create a notification for the user who issued the voucher (if different)
    if voucher.issued_by and voucher.issued_by != request.user:
        create_notification(
            recipient=voucher.issued_by,
            title="Voucher Redeemed",
            message=f"Voucher for {voucher.guest_name} has been redeemed.",
            notification_type="voucher",
            related_object=voucher
        )

    return JsonResponse({
        "status": "success",
        "message": f"Voucher for {voucher.guest_name} validated!",
        "guest": voucher.guest_name,
    })


def voucher_report(request):
    # Check if user has permission to view reports
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to view voucher reports.")
    
    vouchers = Voucher.objects.all().order_by("-created_at")
    return render(request, "dashboard/voucher_report.html", {"vouchers": vouchers})


def issue_voucher_list(request):
    # Check if user has permission to issue vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to issue vouchers.")
    
    guests = Guest.objects.all()
    return render(request, "dashboard/issue_voucher.html", {"guests": guests})


def scan_voucher_page(request):
    """Render the voucher scanning page (form/QR scanner UI)."""
    # Check if user has permission to scan vouchers
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to scan vouchers.")
    
    return render(request, "dashboard/scan_voucher.html")


# ------------------- Base Views -------------------
class BaseNavView(LoginRequiredMixin, TemplateView):
    """Shared base to ensure login and provide navigation context."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["ADMINS_GROUP"] = ADMINS_GROUP
        context["USERS_GROUP"] = USERS_GROUP
        context["STAFF_GROUP"] = STAFF_GROUP
        context["is_admin"] = user_in_group(user, ADMINS_GROUP)
        context["is_staff"] = user_in_group(user, STAFF_GROUP)
        context["is_user"] = user_in_group(user, USERS_GROUP)
        return context


# ------------------- Template Views -------------------
class HomeView(BaseNavView):
    template_name = 'home.html'


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the user in after signup
            return redirect("dashboard:main")  # change to your dashboard homepage
    else:
        form = UserCreationForm()
    return render(request, "auth/signup.html", {"form": form})

class MasterUserView(AdminOnlyView, BaseNavView):
    template_name = 'screens/master_user.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.select_related('userprofile__department').all()
        return context


class MasterLocationView(AdminOnlyView, BaseNavView):
    template_name = 'screens/master_location.html'


class HotelDashboardView(BaseNavView):
    template_name = 'screens/hotel_dashboard.html'


class VoucherPageView(BaseNavView):
    template_name = 'screens/vouchers.html'


class MainDashboardView(BaseNavView):
    template_name = 'dashboard/main.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = User.objects.count()
        context["total_departments"] = Department.objects.count()
        context["total_locations"] = Location.objects.count()
        context["active_complaints"] = ServiceRequest.objects.filter(status="open").count()
        context["resolved_complaints"] = ServiceRequest.objects.filter(status="closed").count()
        context["vouchers_issued"] = Voucher.objects.count()
        context["vouchers_redeemed"] = Voucher.objects.filter(redeemed=True).count()

        complaint_trends = list(
            ServiceRequest.objects.values("status").order_by("status").annotate(count=Count("id"))
        )
        context["complaint_trends"] = json.dumps(complaint_trends)
        return context



# ------------------- Bulk Actions -------------------
@require_http_methods(['POST'])
def bulk_delete_users(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        ids = data.get('ids', [])
        if not request.user.is_authenticated or not user_in_group(request.user, ADMINS_GROUP):
            return Response({'detail': 'forbidden'}, status=403)
        User.objects.filter(id__in=ids).delete()
        return Response({'deleted': len(ids)})
    except Exception as e:
        return Response({'error': str(e)}, status=400)


def export_users_csv(request):
    if not request.user.is_authenticated or not user_in_group(request.user, ADMINS_GROUP):
        return redirect('login')

    users = User.objects.select_related('userprofile__department').all()
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="users.csv"'
    writer = csv.writer(resp)
    writer.writerow(['id', 'username', 'full_name', 'email', 'department', 'is_active'])
    for u in users:
        dept = u.userprofile.department.name if hasattr(u, 'userprofile') and u.userprofile.department else ''
        writer.writerow([u.id, u.username, u.get_full_name(), u.email, dept, u.is_active])
    return resp

def register_guest(request):
    """Enhanced guest registration with automatic voucher generation and QR code"""
    # Check if user has permission to register guests
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        raise PermissionDenied("You don't have permission to register guests.")
    
    if request.method == "POST":
        form = GuestForm(request.POST)
        if form.is_valid():
            try:
                guest = form.save()
                
                # Generate QR code for guest details
                if not guest.details_qr_code:
                    guest.generate_details_qr_code(size='xxlarge')
                
                # Check if voucher was created
                vouchers_created = guest.vouchers.count()
                
                # Create a notification for the user who registered the guest
                create_notification(
                    recipient=request.user,
                    title="Guest Registered",
                    message=f"Guest {guest.full_name} has been registered successfully.",
                    notification_type="info",
                    related_object=guest
                )
                
                return redirect('dashboard:guest_detail', guest_id=guest.id)
            except Exception as e:
                messages.error(request, f"Error registering guest: {str(e)}")
                return render(request, "dashboard/register_guest.html", {"form": form})
    else:
        form = GuestForm()
    return render(request, "dashboard/register_guest.html", {"form": form})
