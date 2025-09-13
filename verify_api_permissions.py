#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('c:\\Users\\varun\\Desktop\\Victoireus internship\\hotel_project')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User, Group
from hotel_app.permissions import IsAdminUser, IsStaffUser, VoucherPermission, GuestPermission

def test_permission_classes():
    print("Testing API permission classes...")
    
    # Create test users
    print("Creating test users...")
    try:
        admin_user = User.objects.create_user(username='perm_admin', password='testpass123')
        staff_user = User.objects.create_user(username='perm_staff', password='testpass123')
        regular_user = User.objects.create_user(username='perm_user', password='testpass123')
        
        # Create groups
        print("Creating test groups...")
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        
        # Assign users to groups
        print("Assigning users to groups...")
        admin_user.groups.add(admins_group)
        staff_user.groups.add(staff_group)
        
        # Test permission classes
        print("\nTesting permission classes...")
        
        # Create mock request objects
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        admin_request = MockRequest(admin_user)
        staff_request = MockRequest(staff_user)
        regular_request = MockRequest(regular_user)
        
        # Test IsAdminUser permission
        print("\nIsAdminUser tests:")
        admin_perm = IsAdminUser()
        print(f"  admin_user has admin permission: {admin_perm.has_permission(admin_request, None)}")
        print(f"  staff_user has admin permission: {admin_perm.has_permission(staff_request, None)}")
        print(f"  regular_user has admin permission: {admin_perm.has_permission(regular_request, None)}")
        
        # Test IsStaffUser permission
        print("\nIsStaffUser tests:")
        staff_perm = IsStaffUser()
        print(f"  admin_user has staff permission: {staff_perm.has_permission(admin_request, None)}")
        print(f"  staff_user has staff permission: {staff_perm.has_permission(staff_request, None)}")
        print(f"  regular_user has staff permission: {staff_perm.has_permission(regular_request, None)}")
        
        print("\nAll permission tests completed successfully!")
        
        # Clean up
        print("\nCleaning up test data...")
        admin_user.delete()
        staff_user.delete()
        regular_user.delete()
        # Note: We're not deleting the groups as they might be used by the application
        
        print("Cleanup completed.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_permission_classes()