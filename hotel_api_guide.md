# Hotel Management System API Guide

## Introduction

This guide provides comprehensive documentation for the Hotel Management System API. The API allows you to interact with various aspects of the hotel management system, including user management, department management, voucher management, guest management, and dashboard analytics.

## Base URL

All API endpoints are relative to the base URL of your deployment. For local development, this is typically:

```
http://localhost:8000
```

## Authentication

The API uses token-based authentication. To access protected endpoints, you need to include an authentication token in the request header.

### Obtaining a Token

To obtain a token, send a POST request to the login endpoint with your credentials:

```
POST /api/auth/login/
```

Request body:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:
```json
{
  "token": "your_auth_token",
  "refresh": "your_refresh_token"
}
```

### Using the Token

Include the token in the Authorization header of your requests:

```
Authorization: Token your_auth_token
```

### Refreshing the Token

To refresh an expired token, send a POST request to the refresh endpoint with your refresh token:

```
POST /api/auth/refresh/
```

Request body:
```json
{
  "refresh": "your_refresh_token"
}
```

Response:
```json
{
  "token": "new_auth_token"
}
```

## API Endpoints

### User Management

#### List Users

```
GET /api/users/
```

Permissions: Admin only

Returns a list of all users in the system.

#### Create User

```
POST /api/users/
```

Permissions: Admin only

Request body:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "first_name": "New",
  "last_name": "User"
}
```

#### Get User

```
GET /api/users/{id}/
```

Permissions: Admin or Self

Returns details of a specific user.

#### Update User

```
PUT /api/users/{id}/
```

Permissions: Admin only

Request body:
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "first_name": "Updated",
  "last_name": "User"
}
```

#### Delete User

```
DELETE /api/users/{id}/
```

Permissions: Admin only

Deletes a specific user.

#### Bulk Delete Users

```
POST /api/bulk-delete-users/
```

Permissions: Admin only

Request body:
```json
{
  "ids": [1, 2, 3]
}
```

#### Export Users

```
GET /export-users/
```

Permissions: Admin only

Exports user data to CSV format.

### Department Management

#### List Departments

```
GET /api/departments/
```

Permissions: Staff

Returns a list of all departments.

#### Create Department

```
POST /api/departments/
```

Permissions: Admin only

Request body:
```json
{
  "name": "New Department",
  "description": "Description of the new department"
}
```

#### Get Department

```
GET /api/departments/{id}/
```

Permissions: Staff

Returns details of a specific department.

#### Update Department

```
PUT /api/departments/{id}/
```

Permissions: Admin only

Request body:
```json
{
  "name": "Updated Department",
  "description": "Updated description"
}
```

#### Delete Department

```
DELETE /api/departments/{id}/
```

Permissions: Admin only

Deletes a specific department.

### Voucher Management

#### List Vouchers

```
GET /api/vouchers/
```

Permissions: Staff

Returns a list of all vouchers.

#### Create Voucher

```
POST /api/vouchers/
```

Permissions: Admin only

Request body:
```json
{
  "guest_name": "John Doe",
  "room_number": "101",
  "voucher_type": "breakfast",
  "check_in_date": "2023-06-01",
  "check_out_date": "2023-06-05",
  "guest": 1
}
```

#### Get Voucher

```
GET /api/vouchers/{id}/
```

Permissions: Staff

Returns details of a specific voucher.

#### Redeem Voucher

```
POST /api/vouchers/{id}/redeem/
```

Permissions: Staff

Manually redeems a voucher.

#### Regenerate QR Code

```
POST /api/vouchers/{id}/regenerate_qr/
```

Permissions: Staff

Regenerates the QR code for a voucher.

#### Voucher Analytics

```
GET /api/vouchers/analytics/
```

Permissions: Staff

Returns analytics data for vouchers, including counts, type distribution, and peak redemption hours.

#### Validate Voucher

```
POST /api/vouchers/validate/
```

Permissions: Staff

Request body:
```json
{
  "voucher_code": "ABC123",
  "scan_location": "Restaurant"
}
```

Validates a voucher and provides detailed information.

#### Simple Voucher Validation

```
GET /api/vouchers/validate/simple/?code={code}
```

Permissions: Staff

Provides basic validation for a voucher.

### Guest Management

#### List Guests

```
GET /api/guests/
```

Permissions: Staff

Returns a list of all guests.

#### Create Guest

```
POST /api/guests/
```

Permissions: Staff

Request body:
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "room_number": "101",
  "checkin_date": "2023-06-01",
  "checkout_date": "2023-06-05",
  "breakfast_included": true
}
```

#### Get Guest

```
GET /api/guests/{id}/
```

Permissions: Staff

Returns details of a specific guest.

### Dashboard

#### Dashboard Overview

```
GET /api/dashboard/overview/
```

Permissions: Staff

Returns overview metrics for the dashboard.

#### Dashboard Complaints

```
GET /api/dashboard/complaints/
```

Permissions: Staff

Returns complaints analytics data.

#### Dashboard Reviews

```
GET /api/dashboard/reviews/
```

Permissions: Staff

Returns reviews analytics data.

## Error Handling

The API returns standard HTTP status codes to indicate the success or failure of a request:

- 200 OK: The request was successful
- 201 Created: The resource was successfully created
- 400 Bad Request: The request was invalid or cannot be served
- 401 Unauthorized: Authentication failed or user doesn't have permissions
- 403 Forbidden: The request is valid but the user doesn't have permissions
- 404 Not Found: The requested resource could not be found
- 500 Internal Server Error: An error occurred on the server

Error responses include a JSON object with an error message:

```json
{
  "error": "Error message"
}
```

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: The page number (default: 1)
- `page_size`: The number of items per page (default: 10)

Example:

```
GET /api/users/?page=2&page_size=20
```

Paginated responses include metadata:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/users/?page=3&page_size=20",
  "previous": "http://localhost:8000/api/users/?page=1&page_size=20",
  "results": [...]
}
```

## Filtering

Many list endpoints support filtering using query parameters. The specific filters available depend on the endpoint.

Example:

```
GET /api/vouchers/?voucher_type=breakfast&is_redeemed=false
```

## Best Practices

1. **Always use HTTPS** in production to secure API communications.
2. **Store tokens securely** and never expose them in client-side code.
3. **Implement token refresh** to maintain user sessions without requiring frequent logins.
4. **Handle rate limiting** by implementing exponential backoff when receiving 429 Too Many Requests responses.
5. **Validate input** before sending it to the API to reduce errors.
6. **Handle errors gracefully** by checking status codes and displaying appropriate messages to users.
7. **Use pagination** for large datasets to improve performance.

## Tools and Resources

- **Postman Collection**: Import the provided Postman collection for easy API testing.
- **cURL Commands**: Use the provided cURL commands for command-line API interaction.
- **API Documentation**: Refer to the API documentation for detailed endpoint specifications.

## Support

For API support, please contact the system administrator or refer to the internal documentation for more information.