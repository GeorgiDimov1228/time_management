# Time Management API

A REST API system for managing employee attendance through RFID card check-ins and check-outs. This application provides a robust backend for workplace time tracking with administrative controls and secure API endpoints.

## Project Overview

This API allows employees to check in and out using RFID cards, tracks attendance records, and provides administrative functionality to manage employee data. Built with FastAPI and PostgreSQL, it offers a modern, secure, and efficient solution for time tracking needs.

## Features

- **RFID-based Check-in/Check-out**: Track employee attendance through RFID card scans
- **User Management**: Create, read, update, and delete employee records
- **Role-based Access Control**: Admin permissions for sensitive operations
- **JWT Authentication**: Secure API access with token-based authentication
- **Attendance Tracking**: Record and retrieve attendance events with timestamps
- **Database Integration**: PostgreSQL storage for all employee and attendance data
- **Docker Support**: Easy deployment with Docker and docker-compose

## Architecture

The application follows a layered architecture pattern:

- **API Layer** (`app/routes/*.py`): Defines all API endpoints and request/response handling
- **Service Layer** (`app/crud.py`): Contains business logic and database operations
- **Data Access Layer** (`app/models.py`, `app/database.py`): Database models and connection handling
- **Schema Layer** (`app/schemas.py`): Data validation and serialization/deserialization
- **Security** (`app/security.py`, `app/auth.py`): Authentication and authorization

## Tech Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation and settings management
- **PostgreSQL**: Relational database
- **JWT**: Token-based authentication
- **Bcrypt**: Password hashing
- **Docker**: Containerization

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (if running locally)

### Environment Setup

1. Create a `.env` file in the project root with the following variables:

```
DATABASE_URL=postgresql://yourusername:yourpassword@db/time_management_db
SECRET_KEY=your-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=adminpassword
```

### Running with Docker

1. Build and start the containers:

```bash
docker-compose up -d
```

2. The API will be available at http://localhost:8000

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication

- **POST /api/token**: Get JWT access token

### User Management (Admin Only)

- **GET /api/users**: List all employees
- **GET /api/users/{id}**: Get employee details
- **POST /api/users**: Create new employee
- **PUT /api/users/{id}**: Update employee information
- **PUT /api/users/{id}/password**: Update employee password
- **DELETE /api/users/{id}**: Delete employee

### Attendance Tracking

- **GET /api/employees/status?rfid={rfid}**: Get employee's current status
- **POST /api/checkin?rfid={rfid}**: Record a check-in event
- **GET /api/checkin**: List all check-in events
- **POST /api/checkout?rfid={rfid}**: Record a check-out event
- **GET /api/checkout**: List all check-out events

## RFID Integration

The system includes an RFID listener (`app/rfid_listener.py`) that can interface with physical RFID readers. This component:

- Runs as a background thread
- Polls configured RFID readers for card scans
- Processes scans by triggering check-in or check-out events
- Supports multiple readers (e.g., entrance and exit points)

To configure RFID readers, update the reader configurations in the `start_rfid_readers` function.

## Testing

The project includes a test script (`test.bash`) for testing API endpoints. Run the script to verify that the API is working correctly:

```bash
bash test.bash
```

## Database Schema

### employees
- `id`: Primary key
- `username`: Unique username
- `email`: Employee email address
- `rfid`: RFID card number
- `hashed_password`: Hashed password (for admin users)
- `is_admin`: Boolean flag for admin permissions

### attendance_events
- `id`: Primary key
- `user_id`: Foreign key to employees
- `event_type`: "checkin" or "checkout"
- `timestamp`: Date and time of the event
- `manual`: Boolean flag for manual entries

## Security Considerations

- All passwords are hashed using bcrypt
- API endpoints protected with JWT authentication
- Admin-only routes require admin role verification
- Default admin user is created on startup for initial setup

## License

[Specify your license here]

## Contributors

[List contributors here]

## Contact

[Your contact information]