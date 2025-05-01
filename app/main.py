# time_management/app/main.py
import os
import datetime
from typing import Any
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request # Import Request
from sqlalchemy import or_ # or_ might not be needed now, but good to have

# --- Database Imports ---
# Keep these as they are, Starlette Admin uses the sync engine
from app.database import sync_engine, Base, SyncSessionLocal
SessionLocal = SyncSessionLocal # Keep alias for default admin creation

# --- App Component Imports ---
from app import models, crud, schemas
from app.routes import users, attendance
from app.auth import router as auth_router

# --- Starlette Admin Imports ---
from starlette_admin.contrib.sqla import Admin as StarletteAdmin, ModelView
from starlette_admin.fields import StringField, EmailField, BooleanField, DateTimeField # Import necessary field types

from app.admin_auth_starlette import AdminAuthProvider # Import the CLASS instead
# from app.admin_auth_starlette import auth_provider # Import the adapted auth provider (we'll create/modify this file next)

# --- Database Table Creation ---
# Keep this section as is
print("Attempting to create database tables if they don't exist...")
try:
    Base.metadata.create_all(bind=sync_engine)
    print("Table creation check complete.")
except Exception as e:
    print(f"Error during table creation check: {e}")

# --- FastAPI App Initialization ---
app = FastAPI(title="Time Management API")
SESSION_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-sessions")
if not SESSION_SECRET_KEY:
    print("WARNING: SECRET_KEY environment variable not set. Using default (unsafe) key.")
    SESSION_SECRET_KEY = "your-secret-key-for-sessions"
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


# --- Starlette Admin Setup ---

# Define Admin Views for Starlette Admin
class EmployeeAdminView(ModelView):
    # Fields to display in the list view
    fields = [
        models.Employee.id,
        models.Employee.username,
        models.Employee.email,
        models.Employee.rfid,
        models.Employee.is_admin
    ]
    sortable_fields = [models.Employee.id, models.Employee.username, models.Employee.is_admin, models.Employee.rfid, models.Employee.email]
    exclude_fields_from_create = [models.Employee.hashed_password, models.Employee.attendance_events, models.Employee.id]
    exclude_fields_from_edit = [models.Employee.hashed_password, models.Employee.attendance_events, models.Employee.id]


class AttendanceEventAdminView(ModelView):
    # Define fields for the CREATE/EDIT forms
    fields = [
        models.AttendanceEvent.employee, # Keep relationship name string for form generation
        models.AttendanceEvent.event_type,
        models.AttendanceEvent.timestamp,
        models.AttendanceEvent.manual
    ]

    exclude_fields_from_create = [models.AttendanceEvent.manual, models.AttendanceEvent.id]
    exclude_fields_from_edit = [models.AttendanceEvent.manual, models.AttendanceEvent.id]

    sortable_fields = [
        models.AttendanceEvent.employee, # Keep relationship name string for form generation
        models.AttendanceEvent.event_type,
        models.AttendanceEvent.timestamp,
        models.AttendanceEvent.manual
    ]
    searchable_fields = [
        # models.AttendanceEvent.employee, # Keep relationship name string for form generation
        models.AttendanceEvent.event_type,
        models.AttendanceEvent.timestamp,
        models.AttendanceEvent.manual
    ]


# Initialize Starlette Admin with the synchronous engine and authentication provider
admin = StarletteAdmin(
    engine=sync_engine,
    title="Time Management Admin",
    base_url="/admin" # Explicitly set base URL
)

auth_provider_instance = AdminAuthProvider() # Create instance
auth_provider_instance.admin = admin # Pass admin instance to provider
admin.auth_provider = auth_provider_instance # Assign provider to admin

# Register Admin Views
admin.add_view(EmployeeAdminView(models.Employee))
admin.add_view(AttendanceEventAdminView(models.AttendanceEvent))


# Mount admin to app
admin.mount_to(app)

# --- Include API Routers ---
# Keep this section as is
app.include_router(auth_router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")

# --- Default Admin User Creation ---
# Keep this function as is, it uses sync CRUD and session
def create_default_admin():
    """
    Creates a default admin user on first startup if one doesn't exist.
    Uses SYNCHRONOUS database operations.
    """
    db = SessionLocal()
    try:
        print("Checking for default admin user...")
        admin_user = crud.get_employee_by_username_sync(db, os.getenv("DEFAULT_ADMIN_USERNAME", "admin"))
        if not admin_user:
            default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
            default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminpassword")

            if not default_password:
                 print("ERROR: DEFAULT_ADMIN_PASSWORD is not set in the environment. Cannot create admin user.")
                 db.close()
                 return

            admin_data = schemas.EmployeeCreate(
                username=default_username,
                email=default_email,
                rfid="DEFAULT_ADMIN_RFID",
                password=default_password,
                is_admin=True
            )
            print(f"Default admin user '{default_username}' not found. Attempting to create...")
            created_user = crud.create_employee_sync(db=db, employee=admin_data)
            if created_user:
                 print(f"Default admin user '{created_user.username}' created successfully.")
            else:
                 print("Failed to create default admin user.")
        else:
            print(f"Default admin user '{admin_user.username}' already exists.")
    except Exception as e:
        print(f"An unexpected error occurred during default admin creation: {e}")
    finally:
        if db:
            db.close()

# --- Run Startup Tasks ---
print("Running startup tasks...")
create_default_admin()
print("Startup tasks complete.")

# --- Optional: Add root endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Time Management API is running"}