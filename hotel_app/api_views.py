from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User, Group
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.db import models
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .models import (
    Department, UserGroup, UserGroupMembership, Location,
    ServiceRequest, BreakfastVoucher, GuestComment, Complaint, Review, Guest
)
from .serializers import (
    UserSerializer, DepartmentSerializer, UserGroupSerializer,
    UserGroupMembershipSerializer, LocationSerializer,
    ServiceRequestSerializer, BreakfastVoucherSerializer,
    GuestCommentSerializer, DashboardMetricsSerializer,
    ComplaintAnalyticsSerializer, ReviewAnalyticsSerializer, ComplaintSerializer, ReviewSerializer,
    GuestSerializer
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