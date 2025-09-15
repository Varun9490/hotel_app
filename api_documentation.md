# Hotel Management System API Documentation

## Authentication

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/auth/login/` | POST | Obtain authentication token | Public |
| `/api/auth/refresh/` | POST | Refresh authentication token | Authenticated |

## User Management

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/users/` | GET | List all users | Admin |
| `/api/users/` | POST | Create a new user | Admin |
| `/api/users/{id}/` | GET | Get user details | Admin or Self |
| `/api/users/{id}/` | PUT | Update user | Admin |
| `/api/users/{id}/` | PATCH | Partially update user | Admin |
| `/api/users/{id}/` | DELETE | Delete user | Admin |

## Department Management

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/departments/` | GET | List all departments | Staff |
| `/api/departments/` | POST | Create a new department | Admin |
| `/api/departments/{id}/` | GET | Get department details | Staff |
| `/api/departments/{id}/` | PUT | Update department | Admin |
| `/api/departments/{id}/` | PATCH | Partially update department | Admin |
| `/api/departments/{id}/` | DELETE | Delete department | Admin |

## User Groups

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/user-groups/` | GET | List all user groups | Staff |
| `/api/user-groups/` | POST | Create a new user group | Admin |
| `/api/user-groups/{id}/` | GET | Get user group details | Staff |
| `/api/user-groups/{id}/` | PUT | Update user group | Admin |
| `/api/user-groups/{id}/` | PATCH | Partially update user group | Admin |
| `/api/user-groups/{id}/` | DELETE | Delete user group | Admin |

## Location Management

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/locations/` | GET | List all locations | Staff |
| `/api/locations/` | POST | Create a new location | Admin |
| `/api/locations/{id}/` | GET | Get location details | Staff |
| `/api/locations/{id}/` | PUT | Update location | Admin |
| `/api/locations/{id}/` | PATCH | Partially update location | Admin |
| `/api/locations/{id}/` | DELETE | Delete location | Admin |

## Service Requests (Complaints)

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/complaints/` | GET | List all service requests | Staff |
| `/api/complaints/` | POST | Create a new service request | Admin |
| `/api/complaints/{id}/` | GET | Get service request details | Staff |
| `/api/complaints/{id}/` | PUT | Update service request | Admin |
| `/api/complaints/{id}/` | PATCH | Partially update service request | Admin |
| `/api/complaints/{id}/` | DELETE | Delete service request | Admin |

## Breakfast Vouchers (Legacy)

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/breakfast-vouchers/` | GET | List all breakfast vouchers | Staff |
| `/api/breakfast-vouchers/` | POST | Create a new breakfast voucher | Admin |
| `/api/breakfast-vouchers/{id}/` | GET | Get breakfast voucher details | Staff |
| `/api/breakfast-vouchers/{id}/` | PUT | Update breakfast voucher | Admin |
| `/api/breakfast-vouchers/{id}/` | PATCH | Partially update breakfast voucher | Admin |
| `/api/breakfast-vouchers/{id}/` | DELETE | Delete breakfast voucher | Admin |
| `/api/breakfast-vouchers/{id}/mark_redeemed/` | POST | Mark voucher as redeemed | Staff |

## Vouchers (New System)

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/vouchers/` | GET | List all vouchers | Staff |
| `/api/vouchers/` | POST | Create a new voucher | Admin |
| `/api/vouchers/{id}/` | GET | Get voucher details | Staff |
| `/api/vouchers/{id}/` | PUT | Update voucher | Admin |
| `/api/vouchers/{id}/` | PATCH | Partially update voucher | Admin |
| `/api/vouchers/{id}/` | DELETE | Delete voucher | Admin |
| `/api/vouchers/{id}/redeem/` | POST | Manually redeem a voucher | Staff |
| `/api/vouchers/{id}/regenerate_qr/` | POST | Regenerate QR code for voucher | Staff |
| `/api/vouchers/analytics/` | GET | Get voucher analytics | Staff |
| `/api/vouchers/validate/` | POST | Validate a voucher (detailed) | Staff |
| `/api/vouchers/validate/simple/` | GET | Simple voucher validation | Staff |

## Voucher Scans

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/voucher-scans/` | GET | List all voucher scans | Staff |
| `/api/voucher-scans/` | POST | Create a new voucher scan | Staff |
| `/api/voucher-scans/{id}/` | GET | Get voucher scan details | Staff |

## Guest Reviews

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/reviews/` | GET | List all guest reviews | Staff |
| `/api/reviews/` | POST | Create a new guest review | Admin |
| `/api/reviews/{id}/` | GET | Get guest review details | Staff |
| `/api/reviews/{id}/` | PUT | Update guest review | Admin |
| `/api/reviews/{id}/` | PATCH | Partially update guest review | Admin |
| `/api/reviews/{id}/` | DELETE | Delete guest review | Admin |

## Guests

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/guests/` | GET | List all guests | Staff |
| `/api/guests/` | POST | Create a new guest | Staff |
| `/api/guests/{id}/` | GET | Get guest details | Staff |
| `/api/guests/{id}/` | PUT | Update guest | Staff |
| `/api/guests/{id}/` | PATCH | Partially update guest | Staff |
| `/api/guests/{id}/` | DELETE | Delete guest | Admin |

## Dashboard

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/dashboard/` | GET | Dashboard API information | Staff |
| `/api/dashboard/overview/` | GET | Get dashboard overview metrics | Staff |
| `/api/dashboard/complaints/` | GET | Get complaints analytics | Staff |
| `/api/dashboard/reviews/` | GET | Get reviews analytics | Staff |

## Legacy Endpoints

| Endpoint | Method | Description | Permission |
|----------|--------|-------------|------------|
| `/api/issue-voucher/{guest_id}/` | POST | Issue voucher to guest | Staff |
| `/api/issue-voucher/` | GET | List guests for voucher issuance | Staff |
| `/api/scan-voucher/` | POST | Scan voucher (legacy) | Staff |
| `/api/scan-voucher-page/` | GET | Get scan voucher page | Staff |
| `/api/voucher-report/` | GET | Get voucher report | Staff |
| `/api/bulk-delete-users/` | POST | Bulk delete users | Admin |
| `/export-users/` | GET | Export users to CSV | Admin |