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
from hotel_app.templatetags.group_filters import has_group, is_admin, is_staff, has_permission

def test_group_functionality():
    print("Testing group functionality...")
    
    # Create test users
    print("Creating test users...")
    try:
        admin_user = User.objects.create_user(username='test_admin', password='testpass123')
        staff_user = User.objects.create_user(username='test_staff', password='testpass123')
        regular_user = User.objects.create_user(username='test_user', password='testpass123')
        
        # Create groups
        print("Creating test groups...")
        admins_group, _ = Group.objects.get_or_create(name='Admins')
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        users_group, _ = Group.objects.get_or_create(name='Users')
        
        # Assign users to groups
        print("Assigning users to groups...")
        admin_user.groups.add(admins_group)
        staff_user.groups.add(staff_group)
        regular_user.groups.add(users_group)
        
        # Test template tags
        print("\nTesting template tags...")
        
        # Test has_group
        print("has_group tests:")
        print(f"  admin_user has 'Admins' group: {has_group(admin_user, 'Admins')}")
        print(f"  staff_user has 'Admins' group: {has_group(staff_user, 'Admins')}")
        print(f"  regular_user has 'Users' group: {has_group(regular_user, 'Users')}")
        
        # Test is_admin
        print("\nis_admin tests:")
        print(f"  admin_user is admin: {is_admin(admin_user)}")
        print(f"  staff_user is admin: {is_admin(staff_user)}")
        print(f"  regular_user is admin: {is_admin(regular_user)}")
        
        # Test is_staff
        print("\nis_staff tests:")
        print(f"  admin_user is staff: {is_staff(admin_user)}")
        print(f"  staff_user is staff: {is_staff(staff_user)}")
        print(f"  regular_user is staff: {is_staff(regular_user)}")
        
        # Test has_permission
        print("\nhas_permission tests:")
        print(f"  admin_user has 'Admins' permission: {has_permission(admin_user, 'Admins')}")
        print(f"  staff_user has 'Staff' permission: {has_permission(staff_user, 'Staff')}")
        print(f"  staff_user has 'Admins' or 'Staff' permission: {has_permission(staff_user, ['Admins', 'Staff'])}")
        print(f"  regular_user has 'Admins' permission: {has_permission(regular_user, 'Admins')}")
        
        print("\nAll tests completed successfully!")
        
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
    test_group_functionality()