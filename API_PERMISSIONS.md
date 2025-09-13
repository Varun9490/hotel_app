# API Permissions Documentation

This document outlines the permission structure for the Hotel Management System API.

## Permission Classes

The API uses custom permission classes defined in `hotel_app/permissions.py`:

1. **IsAdminUser**: Allows access only to admin users
2. **IsStaffUser**: Allows access to admin and staff users
3. **IsAdminOrReadOnly**: Allows read-only access to all authenticated users, write operations only to admin users
4. **IsStaffOrReadOnly**: Allows read-only access to all authenticated users, write operations only to staff users
5. **VoucherPermission**: Custom permission for voucher operations
6. **GuestPermission**: Custom permission for guest operations
7. **UserPermission**: Custom permission for user operations

## API Endpoint Permissions

### User Management (`/api/users/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List all users | GET | IsAdminUser | Admin |
| View user profile | GET | IsAuthenticated (own) or IsAdminUser (any) | User (own), Admin |
| Create user | POST | IsAdminUser | Admin |
| Update user | PUT/PATCH | IsAdminUser | Admin |
| Delete user | DELETE | IsAdminUser | Admin |

### Department Management (`/api/departments/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List departments | GET | IsStaffUser | Staff, Admin |
| View department | GET | IsStaffUser | Staff, Admin |
| Create department | POST | IsAdminUser | Admin |
| Update department | PUT/PATCH | IsAdminUser | Admin |
| Delete department | DELETE | IsAdminUser | Admin |

### User Groups (`/api/user-groups/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List user groups | GET | IsStaffUser | Staff, Admin |
| View user group | GET | IsStaffUser | Staff, Admin |
| Create user group | POST | IsAdminUser | Admin |
| Update user group | PUT/PATCH | IsAdminUser | Admin |
| Delete user group | DELETE | IsAdminUser | Admin |

### Locations (`/api/locations/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List locations | GET | IsStaffUser | Staff, Admin |
| View location | GET | IsStaffUser | Staff, Admin |
| Create location | POST | IsAdminUser | Admin |
| Update location | PUT/PATCH | IsAdminUser | Admin |
| Delete location | DELETE | IsAdminUser | Admin |

### Service Requests (`/api/complaints/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List service requests | GET | IsStaffUser | Staff, Admin |
| View service request | GET | IsStaffUser | Staff, Admin |
| Create service request | POST | IsAdminUser | Admin |
| Update service request | PUT/PATCH | IsAdminUser | Admin |
| Delete service request | DELETE | IsAdminUser | Admin |

### Breakfast Vouchers (`/api/breakfast-vouchers/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List vouchers | GET | IsStaffUser | Staff, Admin |
| View voucher | GET | IsStaffUser | Staff, Admin |
| Create voucher | POST | IsAdminUser | Admin |
| Update voucher | PUT/PATCH | IsAdminUser | Admin |
| Delete voucher | DELETE | IsAdminUser | Admin |
| Mark as redeemed | POST | IsStaffUser | Staff, Admin |

### Guest Comments (`/api/guest-comments/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List comments | GET | IsStaffUser | Staff, Admin |
| View comment | GET | IsStaffUser | Staff, Admin |
| Create comment | POST | IsAdminUser | Admin |
| Update comment | PUT/PATCH | IsAdminUser | Admin |
| Delete comment | DELETE | IsAdminUser | Admin |

### Complaints (`/api/complaints/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List complaints | GET | IsStaffUser | Staff, Admin |
| View complaint | GET | IsStaffUser | Staff, Admin |
| Create complaint | POST | IsAdminUser | Admin |
| Update complaint | PUT/PATCH | IsAdminUser | Admin |
| Delete complaint | DELETE | IsAdminUser | Admin |

### Reviews (`/api/reviews/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List reviews | GET | IsStaffUser | Staff, Admin |
| View review | GET | IsStaffUser | Staff, Admin |
| Create review | POST | IsAdminUser | Admin |
| Update review | PUT/PATCH | IsAdminUser | Admin |
| Delete review | DELETE | IsAdminUser | Admin |

### Guests (`/api/guests/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List guests | GET | IsStaffUser | Staff, Admin |
| View guest | GET | IsStaffUser | Staff, Admin |
| Create guest | POST | IsStaffUser | Staff, Admin |
| Update guest | PUT/PATCH | IsAdminUser | Admin |
| Delete guest | DELETE | IsAdminUser | Admin |
| View guest vouchers | GET | IsStaffUser | Staff, Admin |
| Create guest voucher | POST | IsStaffUser | Staff, Admin |

### Vouchers (`/api/vouchers/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List vouchers | GET | IsStaffUser | Staff, Admin |
| View voucher | GET | IsStaffUser | Staff, Admin |
| Create voucher | POST | IsStaffUser | Staff, Admin |
| Update voucher | PUT/PATCH | IsAdminUser | Admin |
| Delete voucher | DELETE | IsAdminUser | Admin |
| Redeem voucher | POST | IsStaffUser | Staff, Admin |
| Regenerate QR | POST | IsStaffUser | Staff, Admin |
| View analytics | GET | IsStaffUser | Staff, Admin |

### Voucher Scans (`/api/voucher-scans/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| List scans | GET | IsStaffUser | Staff, Admin |
| View scan | GET | IsStaffUser | Staff, Admin |

### Dashboard (`/api/dashboard/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| View dashboard | GET | IsStaffUser | Staff, Admin |
| View overview | GET | IsStaffUser | Staff, Admin |
| View complaints analytics | GET | IsStaffUser | Staff, Admin |
| View reviews analytics | GET | IsStaffUser | Staff, Admin |

### Voucher Validation (`/api/vouchers/validate/`)

| Operation | Method | Permission Required | Allowed Roles |
|-----------|--------|-------------------|---------------|
| Validate voucher | POST | IsStaffUser | Staff, Admin |
| Simple validation | GET | IsStaffUser | Staff, Admin |

## Permission Logic

### Admin Users
- Have access to all endpoints
- Can perform all CRUD operations
- Can manage system configuration

### Staff Users
- Can view and create operational data (guests, vouchers, etc.)
- Cannot delete or modify system configuration
- Cannot modify existing guest or voucher records (only create new ones)

### Regular Users
- Limited or no access to most endpoints
- Cannot perform administrative operations

## Implementation Details

The permission system is implemented using Django REST Framework's permission classes. Each viewset defines its permissions in the `get_permissions()` method, allowing for fine-grained control over different operations.

For example, the `VoucherViewSet` implements different permissions for different actions:

```python
def get_permissions(self):
    if self.action == 'create':
        # Staff and admins can create vouchers
        return [IsStaffUser()]
    elif self.action in ['update', 'partial_update', 'destroy']:
        # Only admins can modify vouchers
        return [IsAdminUser()]
    elif self.action in ['list', 'retrieve']:
        # Staff and admins can view vouchers
        return [IsStaffUser()]
    # ... additional action-specific permissions
```

This approach ensures that permissions are clearly defined and easily maintainable.