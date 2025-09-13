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
    Location, ServiceRequest, Voucher, GuestComment, Guest
)
from hotel_app.serializers import (
    UserSerializer, DepartmentSerializer, UserGroupSerializer,
    UserGroupMembershipSerializer, LocationSerializer,
    ServiceRequestSerializer, GuestCommentSerializer
)
from hotel_app.utils import generate_qr_code, user_in_group, group_required, admin_required
from .forms import GuestForm
from .models import Guest

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
    return render(request, "dashboard/breakfast_vouchers.html", {"vouchers": vouchers})


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

    if created or not voucher.qr_code:
        # Generate QR code with larger size for better visibility
        qr_data = f"Voucher: {voucher.voucher_code}\nGuest: {voucher.guest_name}"
        voucher.qr_image = generate_qr_code(qr_data, size='xlarge')
        voucher.save(update_fields=['qr_image'])

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


def api_gui_view(request):
    return render(request, 'api_gui.html')


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
                
                # Check if voucher was created
                vouchers_created = guest.vouchers.count()
                
                # Prepare success message
                if vouchers_created > 0:
                    messages.success(
                        request, 
                        f"Guest {guest.full_name} registered successfully! "
                        f"{vouchers_created} voucher(s) created."
                    )
                else:
                    messages.success(
                        request,
                        f"Guest {guest.full_name} registered successfully!"
                    )
                
                # Check if guest details QR code was generated
                if guest.details_qr_code:
                    messages.info(
                        request,
                        "Guest details QR code generated successfully! You can view it on the guest details page."
                    )
                
                # Redirect based on user preference or default
                redirect_to = request.POST.get('redirect_to', 'guest_qr_success')
                if redirect_to == 'create_another':
                    return redirect('register_guest')
                elif redirect_to == 'view_vouchers':
                    return redirect('dashboard:vouchers')
                elif redirect_to == 'guest_qr_success':
                    return redirect('guest_qr_success', guest_id=guest.id)
                else:
                    return redirect('dashboard:guests')
            except Exception as e:
                # Add error message and log the exception
                messages.error(request, f"Error saving guest: {str(e)}")
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in guest registration: {str(e)}")
        else:
            # Add form validation errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            
            # Add non-field errors
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = GuestForm()
    
    return render(request, "dashboard/register_guest.html", {
        "form": form,
        "title": "Register New Guest"
    })


def guest_qr_success(request, guest_id):
    """Display guest details and QR code after successful registration"""
    guest = get_object_or_404(Guest, id=guest_id)
    
    # Get associated vouchers
    vouchers = guest.vouchers.all()
    
    # Parse QR data for display
    qr_details = None
    if guest.details_qr_data:
        try:
            qr_details = json.loads(guest.details_qr_data)
        except json.JSONDecodeError:
            qr_details = None
    
    context = {
        'guest': guest,
        'vouchers': vouchers,
        'qr_details': qr_details,
        'title': f'Guest Registration Complete - {guest.full_name}'
    }
    
    return render(request, "dashboard/guest_qr_success.html", context)


@require_http_methods(["POST"])
def generate_guest_qr(request, guest_id):
    """Generate QR code for guest details on demand"""
    # Check if user has permission to generate QR codes
    if not (user_in_group(request.user, ADMINS_GROUP) or user_in_group(request.user, STAFF_GROUP)):
        return JsonResponse({"status": "error", "message": "Permission denied"}, status=403)
    
    guest = get_object_or_404(Guest, id=guest_id)
    
    try:
        success = guest.generate_details_qr_code()
        if success:
            return JsonResponse({
                'success': True,
                'message': 'QR code generated successfully',
                'qr_url': guest.get_details_qr_url(request)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to generate QR code'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error generating QR code: {str(e)}'
        })