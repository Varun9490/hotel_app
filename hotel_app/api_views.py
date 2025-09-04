from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User, Group
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.db import models
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import (
    Department, UserGroup, UserGroupMembership, Location,
    ServiceRequest, BreakfastVoucher, GuestComment, Complaint, Review, Guest,
    Voucher, VoucherScan  # New voucher models
)
from .serializers import (
    UserSerializer, DepartmentSerializer, UserGroupSerializer,
    UserGroupMembershipSerializer, LocationSerializer,
    ServiceRequestSerializer, BreakfastVoucherSerializer,
    GuestCommentSerializer, DashboardMetricsSerializer,
    ComplaintAnalyticsSerializer, ReviewAnalyticsSerializer, ComplaintSerializer, ReviewSerializer,
    GuestSerializer, GuestCreateSerializer,
    # New voucher serializers
    VoucherSerializer, VoucherScanSerializer, VoucherValidationSerializer,
    VoucherValidationResponseSerializer, VoucherCreateSerializer,
    VoucherAnalyticsSerializer, VoucherReportSerializer
)

# Authentication Views
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['name'] = user.get_full_name()
        token['is_admin'] = user.is_superuser or user.groups.filter(name='Admins').exists()
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

# User Management
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admins can modify users
            return [permissions.IsAdminUser()]
        return super().get_permissions()

# Department Management
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

# User Groups
class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

class UserGroupMembershipViewSet(viewsets.ModelViewSet):
    queryset = UserGroupMembership.objects.all()
    serializer_class = UserGroupMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

# Master Location
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

# Complaints (Service Requests)
class ServiceRequestViewSet(viewsets.ModelViewSet):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Admins').exists():
            return ServiceRequest.objects.all()
        return ServiceRequest.objects.filter(
            Q(requester_user=user) | Q(assignee_user=user)
        )

# Food Voucher
class BreakfastVoucherViewSet(viewsets.ModelViewSet):
    queryset = BreakfastVoucher.objects.all()
    serializer_class = BreakfastVoucherSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def mark_redeemed(self, request, pk=None):
        voucher = self.get_object()
        voucher.status = 'redeemed'
        voucher.save()
        
        # Create scan record
        BreakfastVoucherScan.objects.create(
            voucher=voucher,
            source='api',
            scanned_by_user=request.user
        )
        
        return Response({'status': 'voucher redeemed'})

# Guest Reviews
class GuestCommentViewSet(viewsets.ModelViewSet):
    queryset = GuestComment.objects.all()
    serializer_class = GuestCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

# Complaints
class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

# Reviews
class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

# Guests
class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [permissions.IsAuthenticated]

# Dashboard Views
class DashboardOverview(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Calculate metrics
        complaints_count = ServiceRequest.objects.count()
        reviews_count = GuestComment.objects.count()
        vouchers_count = BreakfastVoucher.objects.count()
        pending_requests = ServiceRequest.objects.filter(status='pending').count()
        completed_requests = ServiceRequest.objects.filter(status='completed').count()
        
        data = {
            'complaints_count': complaints_count,
            'reviews_count': reviews_count,
            'vouchers_count': vouchers_count,
            'pending_requests': pending_requests,
            'completed_requests': completed_requests,
        }
        
        serializer = DashboardMetricsSerializer(data)
        return Response(serializer.data)

class DashboardComplaints(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Group complaints by status
        complaints_by_status = ServiceRequest.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Convert to serializer format
        data = [{'status': item['status'], 'count': item['count']} for item in complaints_by_status]
        
        serializer = ComplaintAnalyticsSerializer(data, many=True)
        return Response(serializer.data)

class DashboardReviews(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Group reviews by rating
        reviews_by_rating = GuestComment.objects.exclude(rating__isnull=True).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        # Calculate average rating
        avg_rating = GuestComment.objects.exclude(rating__isnull=True).aggregate(
            avg_rating=Avg('rating')
        )
        
        # Convert to serializer format
        data = [{'rating': item['rating'], 'count': item['count']} for item in reviews_by_rating]
        
        return Response({
            'ratings': data,
            'average_rating': avg_rating['avg_rating'] or 0
        })

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response({
            "message": "This is the dashboard API. Use specific endpoints for data.",
            "endpoints": [
                "/api/dashboard/overview/",
                "/api/dashboard/complaints/",
                "/api/dashboard/reviews/"
            ]
        })

    @action(detail=False, methods=['get'])
    def overview(self, request):
        complaints_count = Complaint.objects.count()
        reviews_count = Review.objects.count()
        vouchers_count = BreakfastVoucher.objects.count()
        return Response({
            'complaints_count': complaints_count,
            'reviews_count': reviews_count,
            'vouchers_count': vouchers_count,
        })

    @action(detail=False, methods=['get'])
    def complaints(self, request):
        # Add more detailed analytics if needed
        complaints_by_status = Complaint.objects.values('status').annotate(count=models.Count('status'))
        return Response(complaints_by_status)

    @action(detail=False, methods=['get'])
    def reviews(self, request):
        # Add more detailed analytics if needed
        from django.db.models import Avg
        average_rating = Review.objects.aggregate(Avg('rating'))
        return Response({'average_rating': average_rating['rating__avg']})


# ========================================
# NEW VOUCHER SYSTEM API VIEWS
# ========================================

class VoucherViewSet(viewsets.ModelViewSet):
    """Complete voucher management API"""
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return VoucherCreateSerializer
        return VoucherSerializer
    
    def get_queryset(self):
        queryset = Voucher.objects.all().select_related('guest', 'location', 'created_by')
        
        # Filter by voucher type
        voucher_type = self.request.query_params.get('type')
        if voucher_type:
            queryset = queryset.filter(voucher_type=voucher_type)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by guest
        guest_id = self.request.query_params.get('guest')
        if guest_id:
            queryset = queryset.filter(guest_id=guest_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(valid_from__gte=from_date)
        if to_date:
            queryset = queryset.filter(valid_to__lte=to_date)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def redeem(self, request, pk=None):
        """Manual voucher redemption endpoint"""
        voucher = self.get_object()
        
        if not voucher.can_be_redeemed_today():
            return Response({
                'success': False,
                'message': 'Voucher cannot be redeemed',
                'error_code': 'CANNOT_REDEEM'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as redeemed
        voucher.mark_as_redeemed(request.user)
        
        # Create scan record
        scan = VoucherScan.objects.create(
            voucher=voucher,
            scanned_by=request.user,
            scan_result='success',
            redemption_successful=True,
            scan_source='manual',
            notes=f'Manual redemption by {request.user.get_full_name()}'
        )
        
        return Response({
            'success': True,
            'message': 'Voucher redeemed successfully',
            'voucher': VoucherSerializer(voucher, context={'request': request}).data,
            'scan_id': scan.id
        })
    
    @action(detail=True, methods=['post'])
    def regenerate_qr(self, request, pk=None):
        """Regenerate QR code for voucher"""
        voucher = self.get_object()
        
        from .utils import generate_voucher_qr_code, generate_voucher_qr_data
        
        # Generate new QR code
        voucher.qr_data = generate_voucher_qr_data(voucher)
        voucher.qr_image = generate_voucher_qr_code(voucher)
        voucher.save()
        
        return Response({
            'success': True,
            'message': 'QR code regenerated successfully',
            'qr_image_url': request.build_absolute_uri(voucher.qr_image.url) if voucher.qr_image else None
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Voucher analytics endpoint"""
        today = timezone.now().date()
        
        # Basic counts
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
        
        # Peak redemption hours (last 30 days)
        from django.db.models import Extract
        peak_hours = list(
            VoucherScan.objects.filter(
                scanned_at__date__gte=today - timedelta(days=30),
                redemption_successful=True
            ).annotate(
                hour=Extract('scanned_at', 'hour')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('-count')[:5].values_list('hour', flat=True)
        )
        
        analytics_data = {
            'total_vouchers': total_vouchers,
            'active_vouchers': active_vouchers,
            'redeemed_vouchers': redeemed_vouchers,
            'expired_vouchers': expired_vouchers,
            'redeemed_today': redeemed_today,
            'vouchers_by_type': vouchers_by_type,
            'peak_redemption_hours': peak_hours,
        }
        
        serializer = VoucherAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class VoucherValidationView(APIView):
    """Main voucher validation endpoint for QR scanning"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Validate voucher from QR scan or voucher code"""
        serializer = VoucherValidationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'valid': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        voucher_code = data.get('voucher_code')
        qr_data = data.get('qr_data')
        scan_location = data.get('scan_location')
        
        # Get client info for audit
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        try:
            voucher = None
            scan_result = 'error'
            error_code = None
            message = 'Validation failed'
            
            # Validate QR data if provided
            if qr_data:
                from .utils import validate_voucher_qr_data
                validation_result = validate_voucher_qr_data(qr_data)
                
                if not validation_result['valid']:
                    scan_result = 'invalid'
                    error_code = 'INVALID_QR'
                    message = validation_result['error']
                else:
                    voucher_code = validation_result['data']['voucher_code']
            
            # Find voucher by code
            if voucher_code and not voucher:
                try:
                    voucher = Voucher.objects.get(voucher_code=voucher_code)
                except Voucher.DoesNotExist:
                    scan_result = 'invalid'
                    error_code = 'VOUCHER_NOT_FOUND'
                    message = 'Voucher not found'
            
            if voucher:
                # Check if voucher can be redeemed
                if not voucher.is_valid():
                    if voucher.redeemed:
                        scan_result = 'already_redeemed'
                        error_code = 'ALREADY_REDEEMED'
                        message = f'Voucher already redeemed on {voucher.redeemed_at.strftime("%Y-%m-%d %H:%M")}'
                    elif voucher.status == 'expired' or voucher.valid_to < timezone.now().date():
                        scan_result = 'expired'
                        error_code = 'EXPIRED'
                        message = f'Voucher expired on {voucher.valid_to}'
                    else:
                        scan_result = 'invalid'
                        error_code = 'INVALID_STATUS'
                        message = f'Voucher status: {voucher.status}'
                elif not voucher.can_be_redeemed_today():
                    scan_result = 'already_redeemed'
                    error_code = 'ALREADY_REDEEMED_TODAY'
                    message = 'Voucher already redeemed today'
                else:
                    # Valid voucher - mark as redeemed
                    voucher.mark_as_redeemed(request.user)
                    scan_result = 'success'
                    message = f'Voucher redeemed successfully for {voucher.guest_name}'
            
            # Create scan record
            scan = VoucherScan.objects.create(
                voucher=voucher,
                scanned_by=request.user,
                scan_result=scan_result,
                redemption_successful=(scan_result == 'success'),
                scan_source='web',
                user_agent=user_agent,
                ip_address=ip_address,
                notes=f'Scan from {scan_location}' if scan_location else None
            )
            
            # Prepare response
            response_data = {
                'valid': scan_result == 'success',
                'message': message,
                'scan_result': scan_result,
            }
            
            if error_code:
                response_data['error_code'] = error_code
            
            if voucher:
                response_data['voucher_details'] = VoucherSerializer(
                    voucher, context={'request': request}
                ).data
            
            response_serializer = VoucherValidationResponseSerializer(response_data)
            
            return Response(response_serializer.data)
            
        except Exception as e:
            # Log error and return generic error response
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Voucher validation error: {str(e)}', exc_info=True)
            
            return Response({
                'valid': False,
                'message': 'System error during validation',
                'error_code': 'SYSTEM_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access for simple validation
def quick_voucher_validation(request, voucher_code):
    """Quick voucher validation endpoint for simple checks"""
    try:
        voucher = Voucher.objects.get(voucher_code=voucher_code)
        
        response_data = {
            'valid': voucher.is_valid(),
            'guest_name': voucher.guest_name,
            'room_number': voucher.room_number,
            'voucher_type': voucher.voucher_type,
            'valid_until': voucher.valid_to.isoformat(),
            'status': voucher.status,
        }
        
        if not voucher.is_valid():
            if voucher.redeemed:
                response_data['message'] = 'Already redeemed'
            elif voucher.valid_to < timezone.now().date():
                response_data['message'] = 'Expired'
            else:
                response_data['message'] = 'Invalid'
        else:
            response_data['message'] = 'Valid voucher'
        
        return JsonResponse(response_data)
        
    except Voucher.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Voucher not found'
        }, status=404)


class VoucherScanViewSet(viewsets.ReadOnlyModelViewSet):
    """Voucher scan history and analytics"""
    queryset = VoucherScan.objects.all()
    serializer_class = VoucherScanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = VoucherScan.objects.all().select_related(
            'voucher', 'voucher__guest', 'scanned_by'
        )
        
        # Filter by voucher
        voucher_id = self.request.query_params.get('voucher')
        if voucher_id:
            queryset = queryset.filter(voucher_id=voucher_id)
        
        # Filter by scan result
        scan_result = self.request.query_params.get('result')
        if scan_result:
            queryset = queryset.filter(scan_result=scan_result)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(scanned_at__date__gte=from_date)
        if to_date:
            queryset = queryset.filter(scanned_at__date__lte=to_date)
        
        return queryset.order_by('-scanned_at')


# Enhanced Guest API with voucher integration
class GuestViewSet(viewsets.ModelViewSet):
    """Enhanced guest management with voucher integration"""
    queryset = Guest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GuestCreateSerializer
        return GuestSerializer
    
    @action(detail=True, methods=['get'])
    def vouchers(self, request, pk=None):
        """Get all vouchers for a guest"""
        guest = self.get_object()
        vouchers = guest.vouchers.all().order_by('-created_at')
        serializer = VoucherSerializer(vouchers, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_voucher(self, request, pk=None):
        """Create a new voucher for this guest"""
        guest = self.get_object()
        
        # Add guest to the data
        data = request.data.copy()
        data['guest'] = guest.id
        data['guest_name'] = guest.full_name or 'Guest'
        data['room_number'] = guest.room_number
        
        serializer = VoucherCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            voucher = serializer.save()
            response_serializer = VoucherSerializer(voucher, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)