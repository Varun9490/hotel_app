"""
Test script to verify API permission checks are working correctly
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

# Add the project directory to the Python path
sys.path.append('c:\\Users\\varun\\Desktop\\Victoireus internship\\hotel_project')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from hotel_app.models import Guest, Voucher

class APIPermissionTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user',
            password='testpass123'
        )
        
        # Create groups
        self.admins_group = Group.objects.create(name='Admins')
        self.staff_group = Group.objects.create(name='Staff')
        
        # Assign users to groups
        self.admin_user.groups.add(self.admins_group)
        self.staff_user.groups.add(self.staff_group)
        
        # Create test data
        self.guest = Guest.objects.create(
            full_name='Test Guest',
            room_number='101',
            breakfast_included=True
        )
        
        self.voucher = Voucher.objects.create(
            guest_name='Test Guest',
            room_number='101',
            valid_dates=['2025-09-15']
        )
        
        # Create API clients
        self.admin_client = APIClient()
        self.staff_client = APIClient()
        self.regular_client = APIClient()
        
        # Authenticate clients
        self.admin_client.force_authenticate(user=self.admin_user)
        self.staff_client.force_authenticate(user=self.staff_user)
        self.regular_client.force_authenticate(user=self.regular_user)

    def test_user_management_permissions(self):
        """Test user management API permissions"""
        url = '/api/users/'
        
        # Admin can list users
        response = self.admin_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff cannot list users
        response = self.staff_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Regular user cannot list users
        response = self.regular_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can create users
        response = self.admin_client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Staff cannot create users
        response = self.staff_client.post(url, {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Regular user cannot create users
        response = self.regular_client.post(url, {
            'username': 'newuser3',
            'email': 'newuser3@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_management_permissions(self):
        """Test guest management API permissions"""
        list_url = '/api/guests/'
        detail_url = f'/api/guests/{self.guest.id}/'
        
        # Admin can list guests
        response = self.admin_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff can list guests
        response = self.staff_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Regular user cannot list guests
        response = self.regular_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can create guests
        response = self.admin_client.post(list_url, {
            'full_name': 'New Guest',
            'room_number': '102'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Staff can create guests
        response = self.staff_client.post(list_url, {
            'full_name': 'New Guest 2',
            'room_number': '103'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Regular user cannot create guests
        response = self.regular_client.post(list_url, {
            'full_name': 'New Guest 3',
            'room_number': '104'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can update guests
        response = self.admin_client.put(detail_url, {
            'full_name': 'Updated Guest',
            'room_number': '105'
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff cannot update guests
        response = self.staff_client.put(detail_url, {
            'full_name': 'Updated Guest 2',
            'room_number': '106'
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Regular user cannot update guests
        response = self.regular_client.put(detail_url, {
            'full_name': 'Updated Guest 3',
            'room_number': '107'
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_voucher_management_permissions(self):
        """Test voucher management API permissions"""
        list_url = '/api/vouchers/'
        detail_url = f'/api/vouchers/{self.voucher.id}/'
        
        # Admin can list vouchers
        response = self.admin_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff can list vouchers
        response = self.staff_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Regular user cannot list vouchers
        response = self.regular_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can create vouchers
        response = self.admin_client.post(list_url, {
            'guest_name': 'New Guest',
            'room_number': '201',
            'valid_dates': ['2025-09-20']
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Staff can create vouchers
        response = self.staff_client.post(list_url, {
            'guest_name': 'New Guest 2',
            'room_number': '202',
            'valid_dates': ['2025-09-21']
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Regular user cannot create vouchers
        response = self.regular_client.post(list_url, {
            'guest_name': 'New Guest 3',
            'room_number': '203',
            'valid_dates': ['2025-09-22']
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can update vouchers
        response = self.admin_client.put(detail_url, {
            'guest_name': 'Updated Guest',
            'room_number': '204',
            'valid_dates': ['2025-09-23']
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff cannot update vouchers
        response = self.staff_client.put(detail_url, {
            'guest_name': 'Updated Guest 2',
            'room_number': '205',
            'valid_dates': ['2025-09-24']
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Regular user cannot update vouchers
        response = self.regular_client.put(detail_url, {
            'guest_name': 'Updated Guest 3',
            'room_number': '206',
            'valid_dates': ['2025-09-25']
        }, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can delete vouchers
        response = self.admin_client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Staff cannot delete vouchers
        # Create a new voucher for testing
        new_voucher = Voucher.objects.create(
            guest_name='Test Guest 2',
            room_number='207',
            valid_dates=['2025-09-26']
        )
        new_detail_url = f'/api/vouchers/{new_voucher.id}/'
        
        response = self.staff_client.delete(new_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Regular user cannot delete vouchers
        response = self.regular_client.delete(new_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_voucher_validation_permissions(self):
        """Test voucher validation API permissions"""
        url = '/api/vouchers/validate/'
        
        # Admin can validate vouchers
        response = self.admin_client.post(url, {
            'voucher_code': self.voucher.voucher_code
        })
        # Should get a validation response, not a permission error
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Staff can validate vouchers
        response = self.staff_client.post(url, {
            'voucher_code': self.voucher.voucher_code
        })
        # Should get a validation response, not a permission error
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Regular user cannot validate vouchers
        response = self.regular_client.post(url, {
            'voucher_code': self.voucher.voucher_code
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_permissions(self):
        """Test dashboard API permissions"""
        url = '/api/dashboard/overview/'
        
        # Admin can access dashboard
        response = self.admin_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff can access dashboard
        response = self.staff_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Regular user cannot access dashboard
        response = self.regular_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_only_permissions(self):
        """Test read-only permissions for authenticated users"""
        # Create a voucher that all users can potentially view
        voucher = Voucher.objects.create(
            guest_name='Public Guest',
            room_number='301',
            valid_dates=['2025-09-30']
        )
        
        detail_url = f'/api/vouchers/{voucher.id}/'
        
        # Admin can view voucher detail
        response = self.admin_client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff can view voucher detail
        response = self.staff_client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Regular user cannot view voucher detail
        response = self.regular_client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

if __name__ == '__main__':
    import unittest
    unittest.main()