# Time Management System - Test Documentation

This document provides information about the test suite, how to run tests, and what functionality is being tested.

## Test Structure

Our test suite consists of:

- `test_auth.py`: Tests for authentication functionality
- `test_users.py`: Tests for user management operations
- `test_attendance.py`: Tests for attendance tracking features

## Environment Setup

Tests use SQLite as a database backend for faster execution and isolation.

### Prerequisites

- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt`)
- `greenlet` library installed (required for async SQLAlchemy operations)

## Running Tests

### Running All Tests

```bash
# Create virtual environment
python -m venv venv
# Activate virtual environment
source venv/bin/activate
# From the project root:
PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
```

### Running Specific Test Files

```bash
# Authentication tests
PYTHONPATH=$PYTHONPATH:. pytest tests/test_auth.py -v

# User management tests
PYTHONPATH=$PYTHONPATH:. pytest tests/test_users.py -v

# Attendance tests
PYTHONPATH=$PYTHONPATH:. pytest tests/test_attendance.py -v
```

### Clearing Test Database

To start with a fresh database:

```bash
rm -f test.db && PYTHONPATH=$PYTHONPATH:. pytest tests/ -v
```

## What We're Testing

### Authentication Tests (`test_auth.py`)

Tests the authentication mechanisms of the application:

- Login functionality with valid credentials
- Login failure with incorrect password
- Login failure with nonexistent users
- Protected routes access control with and without valid tokens
- Token validation and expiration

### User Management Tests (`test_users.py`)

Tests the CRUD operations for employees/users:

- User creation with proper validation
- Retrieving user listings
- Retrieving individual users by ID
- Updating user information
- Deleting users
- Password change functionality
- Authorization checks for admin-only operations

### Attendance Tests (`test_attendance.py`)

Tests the time tracking functionality:

- Check-in operations with valid RFID
- Check-out operations
- Validation of invalid RFID numbers
- Retrieving attendance records (individual and all)
- Time tracking calculations

## Test Fixtures

The tests use several fixtures defined in `conftest.py`:

- `client`: Test client for making HTTP requests
- `db_session`: Database session for test operations
- `test_user`: Regular user account for testing
- `test_admin`: Admin user account for testing

## Troubleshooting

### Common Issues

1. **"No such table" errors**: Ensure the test database is being created properly. Use the command with `rm -f test.db` to reset.

2. **Import errors**: Check that PYTHONPATH is set correctly when running tests.

3. **Authentication failures**: Verify that token handling is working correctly and that the test users are being created with proper credentials.

4. **Missing dependencies**: Ensure all requirements are installed, particularly `greenlet` which is needed for async SQLAlchemy. 