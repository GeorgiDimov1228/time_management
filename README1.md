# Time Management API Documentation

This document provides an overview of the RESTful API endpoints for the Time Management system. The API allows employees to check in and check out using their RFID cards and provides administrators with endpoints to manage users and attendance records.

---

## Base URL

All endpoints are relative to:  
`https://your-domain.com/api`

---

## 1. Users Endpoint

Endpoints for managing user records. Each user should have a unique RFID, along with other identifying information.

### GET `/users`
- **Description:** Retrieve a list of all users.
- **Method:** GET
- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "username": "jdoe",
      "email": "jdoe@example.com",
      "rfid": "1234567890"
    },
    {
      "id": 2,
      "username": "asmith",
      "email": "asmith@example.com",
      "rfid": "0987654321"
    }
  ]



### GET /users/{id}
- **Description**: Retrieve details for a specific user.
- **Method**: GET
- URL Parameter: id (integer) – the unique ID of the user.
- **Response Example:**
```json
{
  "id": 1,
  "username": "jdoe",
  "email": "jdoe@example.com",
  "rfid": "1234567890"
}
```



### POST /users
- **Description**: Create a new user.
- Method: POST
- Request Body:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "rfid": "1122334455",
  "password": "yourpassword"
}
```
- **Response Example**:
```json

{
  "id": 3,
  "username": "newuser",
  "email": "newuser@example.com",
  "rfid": "1122334455"
}
```
### PUT /users/{id}
- **Description**: Update an existing user's information.
- **Method**: PUT
- URL Parameter: id – the unique ID of the user.
- Request Body:
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "rfid": "9988776655"
}
```
**Response Example:**
```json
{
  "id": 3,
  "username": "updateduser",
  "email": "updated@example.com",
  "rfid": "9988776655"
}
```
### DELETE /users/{id}
- Description: Delete a user.
- Method: DELETE
- URL Parameter: id – the unique ID of the user.
**Response: HTTP 204 No Content**
## 2. Check-In Endpoint
Endpoints for recording and retrieving check-in events.

### POST /checkin
- Description: Record a check-in event for an employee.
- Method: POST
- Request Body:
```json
{
  "rfid": "1234567890"
}
```
Notes: The system will look up the user by RFID and create a check-in event with the current timestamp.
Response Example:
```json
{
  "id": 101,
  "user_id": 1,
  "event_type": "checkin",
  "timestamp": "2025-02-27T08:00:00Z",
  "manual": false
}
```
### GET /checkin
Description: Retrieve a list of all check-in events.
Method: GET
Response Example:

```json

[
  {
    "id": 101,
    "user_id": 1,
    "event_type": "checkin",
    "timestamp": "2025-02-27T08:00:00Z",
    "manual": false
  },
  {
    "id": 102,
    "user_id": 2,
    "event_type": "checkin",
    "timestamp": "2025-02-27T08:05:00Z",
    "manual": false
  }
]
```
## 3. Check-Out Endpoint
Endpoints for recording and retrieving check-out events.

### POST /checkout
Description: Record a check-out event for an employee.
Method: POST
Request Body:
```json
{
  "rfid": "1234567890"
}
```
Notes: Similar to check-in, the system will look up the user by RFID and create a check-out event.
Response Example:

```json
{
  "id": 201,
  "user_id": 1,
  "event_type": "checkout",
  "timestamp": "2025-02-27T12:00:00Z",
  "manual": false
}
```
GET /checkout
Description: Retrieve a list of all check-out events.
Method: GET
Response Example:
```json
[
  {
    "id": 201,
    "user_id": 1,
    "event_type": "checkout",
    "timestamp": "2025-02-27T12:00:00Z",
    "manual": false
  },
  {
    "id": 202,
    "user_id": 2,
    "event_type": "checkout",
    "timestamp": "2025-02-27T12:05:00Z",
    "manual": false
  }
]
```
## 4. Additional Considerations
Admin & Manual Overrides:
An administrative interface (via a secure dashboard or built-in admin tool) should allow administrators to view all attendance records, perform manual check-in/check-out overrides, and handle cases where an RFID is broken or lost.

Authentication & Security:
Protect endpoints using token-based authentication (e.g., JWT). Only authorized personnel (admins) should have access to sensitive endpoints (e.g., user management and full attendance logs).

Error Handling:

400 Bad Request – Invalid payload or missing required fields.
404 Not Found – User or attendance record not found.
401 Unauthorized – Missing or invalid authentication token.
Example Usage with curl
Recording a Check-In:

```
curl -X POST "https://your-domain.com/api/checkin" \
     -H "Content-Type: application/json" \
     -d '{"rfid": "1234567890"}'
````
Retrieving All Check-Ins:

```
curl "https://your-domain.com/api/checkin"
```
This documentation outlines the necessary endpoints to support your system's basic operations. As your project evolves, you may add additional endpoints or refine the request/response formats to suit your needs.
