from rest_framework import permissions
from django.conf import settings

def user_in_group(user, group_name):
    """Check if user is in a specific group"""
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists())

class IsAdminUser(permissions.BasePermission):
    """
    Permission check for admin users.
    Allows access only to admin users.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user belongs to admin group
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        return user_in_group(request.user, admins_group)

class IsStaffUser(permissions.BasePermission):
    """
    Permission check for staff users.
    Allows access to admin and staff users.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user belongs to admin or staff group
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        staff_group = getattr(settings, 'STAFF_GROUP', 'Staff')
        
        return (user_in_group(request.user, admins_group) or 
                user_in_group(request.user, staff_group))

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission check that allows read-only access to all authenticated users,
    but write operations only to admin users.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Allow read-only operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write operations only for admin users
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        return user_in_group(request.user, admins_group)

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission check that allows read-only access to all authenticated users,
    but write operations only to staff users.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Allow read-only operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write operations only for staff users
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        staff_group = getattr(settings, 'STAFF_GROUP', 'Staff')
        
        return (user_in_group(request.user, admins_group) or 
                user_in_group(request.user, staff_group))

# Specific permissions for different models
class VoucherPermission(permissions.BasePermission):
    """
    Custom permission for voucher operations.
    Staff and Admin users can view and create vouchers.
    Only Admin users can delete vouchers.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Allow all authenticated users to list and retrieve
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Create, update operations for staff and admin
        if request.method in ['POST', 'PUT', 'PATCH']:
            admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
            staff_group = getattr(settings, 'STAFF_GROUP', 'Staff')
            return (user_in_group(request.user, admins_group) or 
                    user_in_group(request.user, staff_group))
        
        # Delete operations only for admin
        if request.method == 'DELETE':
            admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
            return user_in_group(request.user, admins_group)
        
        return False

class GuestPermission(permissions.BasePermission):
    """
    Custom permission for guest operations.
    Staff and Admin users can view and manage guests.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Allow all authenticated users to list and retrieve
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # All operations for staff and admin
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        staff_group = getattr(settings, 'STAFF_GROUP', 'Staff')
        return (user_in_group(request.user, admins_group) or 
                user_in_group(request.user, staff_group))

class UserPermission(permissions.BasePermission):
    """
    Custom permission for user operations.
    Only Admin users can manage users.
    """
    
    def has_permission(self, request, view):
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Allow authenticated users to view their own data
        if request.method in permissions.SAFE_METHODS and view.basename == 'users':
            # For list view, only admins
            if view.action == 'list':
                admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
                return user_in_group(request.user, admins_group)
            # For detail view, allow users to view their own data
            elif view.action == 'retrieve' and 'pk' in view.kwargs:
                return str(request.user.pk) == str(view.kwargs['pk'])
        
        # All other operations only for admin users
        admins_group = getattr(settings, 'ADMINS_GROUP', 'Admins')
        return user_in_group(request.user, admins_group)