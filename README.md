# Time Management System

A comprehensive employee time tracking solution with RFID-based attendance management and a custom admin interface.

## Overview

The Time Management System is designed to track employee attendance through RFID card check-ins and check-outs. It features a custom web-based admin interface that provides administrators with tools for managing employees, monitoring attendance, generating reports, and performing manual attendance adjustments.

## Key Features

### Core Functionality
- **RFID-based Check-in/Check-out**: Track employee attendance using RFID card scans
- **Automatic Event Detection**: System intelligently determines whether to record a check-in or check-out
- **Cooldown Prevention**: Prevents duplicate scans within a configurable time window
- **UTC Timezone Support**: Consistent timestamp handling across different time zones

### Custom Admin Interface
- **Dashboard**: Real-time overview of today's attendance statistics
- **Employee Management**: CRUD operations for managing employee records
- **Attendance Monitoring**: View, filter, and edit attendance records
- **Manual Check-in/out**: Record attendance events manually when needed
- **Advanced Filtering**: Filter attendance by date range, employee, event type, etc.
- **Export Tools**: Generate and download CSV exports of attendance data
- **Reporting**: Create comprehensive attendance reports with employee statistics

### Security
- **Role-based Access Control**: Admin permissions for sensitive operations
- **JWT Authentication**: Secure API access with token-based authentication
- **Cookie-based Session Management**: Secure admin interface sessions
- **Password Hashing**: All passwords stored securely using bcrypt

### Integration Capabilities
- **Hardware Integration**: Compatible with Arduino, ESP32/ESP8266 RFID readers
- **Multiple Integration Methods**: Direct API, bridge middleware, or RFID listener
- **Testing Tools**: Mock RFID reader for testing without physical hardware

## System Architecture

The application follows a modern architecture pattern:

- **API Layer**: FastAPI routes defining all endpoints and request/response handling
- **Business Logic Layer**: CRUD operations and core business functionality
- **Data Layer**: SQLAlchemy ORM with PostgreSQL database
- **Schema Layer**: Pydantic models for data validation and serialization
- **Security Layer**: Authentication and authorization mechanisms
- **UI Layer**: Custom admin interface with Jinja2 templates and Bootstrap 5

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens and cookie-based sessions
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **RFID Hardware Support**: Arduino/ESP32/ESP8266

## Database Schema

### employees
- `id`: Primary key
- `username`: Unique username
- `email`: Employee email address
- `rfid`: RFID card number
- `hashed_password`: Encrypted password
- `is_admin`: Boolean flag for admin privileges

### attendance_events
- `id`: Primary key
- `user_id`: Foreign key to employees
- `event_type`: "checkin" or "checkout"
- `timestamp`: Date and time of the event
- `manual`: Boolean flag indicating manual or automatic entry
- `notes`: Optional text field for additional information

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+
- PostgreSQL (if running without Docker)

### Environment Setup

1. Create a `.env` file in the project root with:

```
DATABASE_URL=postgresql://username:password@localhost/time_management_db
SECRET_KEY=your-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=adminpassword
ACTION_COOLDOWN_SECONDS=10
```

### Running with Docker

```bash
docker compose up -d
```

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up the database:

```bash
# Create database if needed
createdb time_management_db
```

3. Run the application:

```bash
uvicorn app.main:app --reload
```

## Admin Interface

The custom admin interface is accessible at `/admin` and provides the following functionality:

### Dashboard
- Overview of current day attendance statistics
- Recent activity feed
- Employee count and check-in/out summary

### Employee Management
- List all employees with search and filtering
- Add new employees with role assignment
- Edit existing employee details
- Reset employee passwords
- Delete employees (with confirmation)

### Attendance Management
- View all attendance records
- Filter by date range, employee, event type, etc.
- Quick filters for today, this week, this month, and last month
- Edit attendance records (change timestamp, event type, etc.)
- Add manual attendance entries
- Delete incorrect entries

### Data Export & Reporting
- Export attendance data as CSV with configurable filters
- Generate comprehensive reports with employee statistics
- Include/exclude detailed entries in reports
- Quick export options for common date ranges

## API Endpoints

The system exposes REST API endpoints for integration:

### Authentication
- `POST /api/token`: Obtain JWT access token

### User Management
- `GET /api/users`: List employees
- `GET /api/users/{id}`: Get employee details
- `POST /api/users`: Create employee
- `PUT /api/users/{id}`: Update employee
- `DELETE /api/users/{id}`: Delete employee

### Attendance
- `POST /api/scan`: Process RFID scan (auto-detects check-in/out)
- `GET /api/employees/status`: Get employee status
- `POST /api/checkin`: Manual check-in
- `POST /api/checkout`: Manual check-out
- `GET /api/filtered`: Get filtered attendance records
- `GET /api/export/csv`: Export attendance as CSV
- `GET /api/admin/report`: Generate attendance report

## RFID Integration

### Direct API Integration
Network-enabled RFID readers can directly call the API endpoints.

### RFID Bridge
For non-networked readers, use the bridge script in `serial_portRead/bridge.py`.

## Security Considerations

- All passwords are hashed using bcrypt
- API endpoints protected with JWT authentication
- Admin-only routes require admin role verification
- Default admin user is created on startup for initial setup
- Auth tokens with configurable expiration
- Cookie-based authentication for the admin UI

## Testing

Use the following scripts to test the system:

- `test.bash`: Test API endpoints
- `mock_rfid_reader.py`: Simulate RFID scans