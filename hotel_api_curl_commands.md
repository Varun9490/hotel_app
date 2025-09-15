# Hotel Management System API - cURL Commands

## Authentication

### Login
```bash
curl -X POST \
  http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "your_password"
}'
```

### Refresh Token
```bash
curl -X POST \
  http://localhost:8000/api/auth/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{
    "refresh": "your_refresh_token"
}'
```

## User Management

### List Users
```bash
curl -X GET \
  http://localhost:8000/api/users/ \
  -H 'Authorization: Token your_auth_token'
```

### Create User
```bash
curl -X POST \
  http://localhost:8000/api/users/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123",
    "first_name": "New",
    "last_name": "User"
}'
```

### Get User
```bash
curl -X GET \
  http://localhost:8000/api/users/1/ \
  -H 'Authorization: Token your_auth_token'
```

### Update User
```bash
curl -X PUT \
  http://localhost:8000/api/users/1/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "updateduser",
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "User"
}'
```

### Delete User
```bash
curl -X DELETE \
  http://localhost:8000/api/users/1/ \
  -H 'Authorization: Token your_auth_token'
```

### Bulk Delete Users
```bash
curl -X POST \
  http://localhost:8000/api/bulk-delete-users/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "ids": [1, 2, 3]
}'
```

### Export Users
```bash
curl -X GET \
  http://localhost:8000/export-users/ \
  -H 'Authorization: Token your_auth_token'
```

## Department Management

### List Departments
```bash
curl -X GET \
  http://localhost:8000/api/departments/ \
  -H 'Authorization: Token your_auth_token'
```

### Create Department
```bash
curl -X POST \
  http://localhost:8000/api/departments/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "New Department",
    "description": "Description of the new department"
}'
```

### Get Department
```bash
curl -X GET \
  http://localhost:8000/api/departments/1/ \
  -H 'Authorization: Token your_auth_token'
```

### Update Department
```bash
curl -X PUT \
  http://localhost:8000/api/departments/1/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Updated Department",
    "description": "Updated description"
}'
```

### Delete Department
```bash
curl -X DELETE \
  http://localhost:8000/api/departments/1/ \
  -H 'Authorization: Token your_auth_token'
```

## Voucher Management

### List Vouchers
```bash
curl -X GET \
  http://localhost:8000/api/vouchers/ \
  -H 'Authorization: Token your_auth_token'
```

### Create Voucher
```bash
curl -X POST \
  http://localhost:8000/api/vouchers/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "guest_name": "John Doe",
    "room_number": "101",
    "voucher_type": "breakfast",
    "check_in_date": "2023-06-01",
    "check_out_date": "2023-06-05",
    "guest": 1
}'
```

### Get Voucher
```bash
curl -X GET \
  http://localhost:8000/api/vouchers/1/ \
  -H 'Authorization: Token your_auth_token'
```

### Redeem Voucher
```bash
curl -X POST \
  http://localhost:8000/api/vouchers/1/redeem/ \
  -H 'Authorization: Token your_auth_token'
```

### Regenerate QR Code
```bash
curl -X POST \
  http://localhost:8000/api/vouchers/1/regenerate_qr/ \
  -H 'Authorization: Token your_auth_token'
```

### Voucher Analytics
```bash
curl -X GET \
  http://localhost:8000/api/vouchers/analytics/ \
  -H 'Authorization: Token your_auth_token'
```

### Validate Voucher
```bash
curl -X POST \
  http://localhost:8000/api/vouchers/validate/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "voucher_code": "ABC123",
    "scan_location": "Restaurant"
}'
```

### Simple Voucher Validation
```bash
curl -X GET \
  "http://localhost:8000/api/vouchers/validate/simple/?code=ABC123" \
  -H 'Authorization: Token your_auth_token'
```

## Guest Management

### List Guests
```bash
curl -X GET \
  http://localhost:8000/api/guests/ \
  -H 'Authorization: Token your_auth_token'
```

### Create Guest
```bash
curl -X POST \
  http://localhost:8000/api/guests/ \
  -H 'Authorization: Token your_auth_token' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "room_number": "101",
    "checkin_date": "2023-06-01",
    "checkout_date": "2023-06-05",
    "breakfast_included": true
}'
```

### Get Guest
```bash
curl -X GET \
  http://localhost:8000/api/guests/1/ \
  -H 'Authorization: Token your_auth_token'
```

## Dashboard

### Dashboard Overview
```bash
curl -X GET \
  http://localhost:8000/api/dashboard/overview/ \
  -H 'Authorization: Token your_auth_token'
```

### Dashboard Complaints
```bash
curl -X GET \
  http://localhost:8000/api/dashboard/complaints/ \
  -H 'Authorization: Token your_auth_token'
```

### Dashboard Reviews
```bash
curl -X GET \
  http://localhost:8000/api/dashboard/reviews/ \
  -H 'Authorization: Token your_auth_token'
```