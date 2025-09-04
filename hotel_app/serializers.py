from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Department, UserGroup, UserProfile, UserGroupMembership,
    Building, Floor, LocationFamily, LocationType, Location,
    RequestFamily, WorkFamily, Workflow, WorkflowStep, WorkflowTransition,
    Checklist, ChecklistItem, RequestType, ServiceRequest, 
    ServiceRequestStep, ServiceRequestChecklist,
    Guest, GuestComment,
    GymMember, GymVisitor, GymVisit,
    BreakfastVoucher, BreakfastVoucherScan,
    Complaint, Review
)

# -------------------
# Core User & Groups
# -------------------

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name',
            'is_active', 'date_joined'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get("username"),
            email=validated_data.get("email"),
            password=validated_data.get("password"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        return user


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'


class UserGroupMembershipSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    group_details = UserGroupSerializer(source='group', read_only=True)

    class Meta:
        model = UserGroupMembership
        fields = '__all__'


# -------------------
# Locations
# -------------------

class LocationSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    floor_number = serializers.IntegerField(source='floor.floor_number', read_only=True)

    class Meta:
        model = Location
        fields = '__all__'


# -------------------
# Service Requests
# -------------------

class ServiceRequestSerializer(serializers.ModelSerializer):
    request_type_name = serializers.CharField(source='request_type.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    requester_name = serializers.CharField(source='requester_user.get_full_name', read_only=True)
    assignee_name = serializers.CharField(source='assignee_user.get_full_name', read_only=True)

    class Meta:
        model = ServiceRequest
        fields = '__all__'


# -------------------
# Guest & Vouchers
# -------------------

class BreakfastVoucherSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = BreakfastVoucher
        fields = '__all__'


class GuestCommentSerializer(serializers.ModelSerializer):
    guest_name = serializers.CharField(source='guest.full_name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = GuestComment
        fields = '__all__'


class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'


# -------------------
# Dashboard Analytics
# -------------------

class DashboardMetricsSerializer(serializers.Serializer):
    complaints_count = serializers.IntegerField()
    reviews_count = serializers.IntegerField()
    vouchers_count = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()


class ComplaintAnalyticsSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()


class ReviewAnalyticsSerializer(serializers.Serializer):
    rating = serializers.IntegerField()
    count = serializers.IntegerField()


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
