# time_management/app/main.py
import os
import datetime
import asyncio # Import asyncio for potential future use in startup events
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

# --- Database Imports ---
# Import sync engine and session for SQLAdmin and initial setup
# Import Base for table creation
# Import AsyncSessionLocal for potential type hinting or future async startup tasks
from app.database import sync_engine, Base, SyncSessionLocal, AsyncSessionLocal
# Alias SyncSessionLocal for easier use in create_default_admin
SessionLocal = SyncSessionLocal

# --- App Component Imports ---
from app import models, crud, schemas
from app.routes import users, attendance
from app.auth import router as auth_router

# --- SQLAdmin Imports ---
from sqladmin import Admin, ModelView
from app.admin_auth import authentication_backend # Import the custom auth backend

# --- Database Table Creation ---
# Create tables using the synchronous engine if they don't exist.
# NOTE: For production, consider using Alembic migrations instead.
print("Attempting to create database tables if they don't exist...")
try:
    Base.metadata.create_all(bind=sync_engine)
    print("Table creation check complete.")
except Exception as e:
    print(f"Error during table creation check: {e}")
    # Depending on the error, you might want to exit or handle it differently

# --- FastAPI App Initialization ---
app = FastAPI(title="Time Management API")
SESSION_SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-sessions") # Ensure SECRET_KEY is set in .env
if not SESSION_SECRET_KEY:
    print("WARNING: SECRET_KEY environment variable not set. Using default (unsafe) key.")
    SESSION_SECRET_KEY = "your-secret-key-for-sessions" # Fallback, but log a warning
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)


# --- SQLAdmin Setup ---

# Define Admin Views (keep as previously defined)
class EmployeeAdmin(ModelView, model=models.Employee):
    column_list = [models.Employee.id, models.Employee.username, models.Employee.email, models.Employee.rfid, models.Employee.is_admin]
    column_labels = { models.Employee.id: "ID", models.Employee.username: 'Username', models.Employee.email: 'Email', models.Employee.rfid: 'RFID', models.Employee.is_admin: 'Admin' }
    column_searchable_list = [models.Employee.username, models.Employee.rfid, models.Employee.email]
    column_sortable_list = [models.Employee.id, models.Employee.username, models.Employee.is_admin, models.Employee.rfid, models.Employee.email]
    form_excluded_columns = [models.Employee.hashed_password, models.Employee.attendance_events]
    name = "Employee"; name_plural = "Employees"; icon = "fa-solid fa-user"

class AttendanceEventAdmin(ModelView, model=models.AttendanceEvent):
    column_list = [ models.AttendanceEvent.id, 'employee.username', models.AttendanceEvent.event_type, models.AttendanceEvent.timestamp, models.AttendanceEvent.manual ]
    column_labels = { models.AttendanceEvent.id: "ID", 'employee.username': 'Username', models.AttendanceEvent.event_type: 'Type', models.AttendanceEvent.timestamp: 'Timestamp', models.AttendanceEvent.manual: 'Manual' }
    form_excluded_columns = [models.AttendanceEvent.manual] # Manual is auto-set
    column_formatters = { models.AttendanceEvent.timestamp: lambda m, a: getattr(m, a).strftime("%Y-%m-%d %H:%M:%S") if getattr(m, a) else "" }
    column_formatters_detail = column_formatters # Use same formatters for detail view
    column_sortable_list = [models.AttendanceEvent.id, models.AttendanceEvent.timestamp, models.AttendanceEvent.event_type, 'employee.username', models.AttendanceEvent.manual]
    column_searchable_list = [ models.AttendanceEvent.event_type, 'employee.username' ]
    column_details_list = [ models.AttendanceEvent.id, 'employee.username', models.AttendanceEvent.event_type, models.AttendanceEvent.timestamp, models.AttendanceEvent.manual ]
    column_filters = [models.AttendanceEvent.event_type, models.AttendanceEvent.manual, models.AttendanceEvent.employee]
    name = "Attendance"; name_plural = "Attendance"; icon = "fa-solid fa-clock"


# Initialize Admin with the synchronous engine and authentication backend
admin = Admin(app=app, engine=sync_engine, authentication_backend=authentication_backend)

# Register Admin Views
admin.add_view(EmployeeAdmin)
admin.add_view(AttendanceEventAdmin)

# --- Include API Routers ---
# Note the dependencies used within each router (sync vs async)
app.include_router(auth_router, prefix="/api")       
app.include_router(users.router, prefix="/api")       
app.include_router(attendance.router, prefix="/api")  


# --- Default Admin User Creation ---
def create_default_admin():
    """
    Creates a default admin user on first startup if one doesn't exist.
    Uses SYNCHRONOUS database operations by calling specifically named sync CRUD functions.
    """
    db = SessionLocal() # Use the synchronous session
    try:
        print("Checking for default admin user...")
        # Call the SYNCHRONOUS version explicitly
        admin_user = crud.get_employee_by_username_sync(db, os.getenv("DEFAULT_ADMIN_USERNAME", "admin"))
        if not admin_user:
            default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
            default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminpassword")

            if not default_password:
                 print("ERROR: DEFAULT_ADMIN_PASSWORD is not set in the environment. Cannot create admin user.")
                 db.close() # Close session before returning
                 return

            admin_data = schemas.EmployeeCreate(
                username=default_username,
                email=default_email,
                rfid="DEFAULT_ADMIN_RFID", # Assign a unique default RFID
                password=default_password,
                is_admin=True
            )
            print(f"Default admin user '{default_username}' not found. Attempting to create...")
            # Call the SYNCHRONOUS version explicitly
            created_user = crud.create_employee_sync(db=db, employee=admin_data)
            if created_user:
                 print(f"Default admin user '{created_user.username}' created successfully.")
            else:
                 print("Failed to create default admin user (sync crud function might have returned None).")
        else:
            print(f"Default admin user '{admin_user.username}' already exists.")
    except Exception as e:
        # Catch potential errors during the sync operation
        print(f"An unexpected error occurred during default admin creation: {e}")
    finally:
        # Ensure the synchronous session is always closed
        if db:
            db.close()

# --- Run Startup Tasks ---
print("Running startup tasks...")
create_default_admin()
print("Startup tasks complete.")

# --- Optional: Add root endpoint for basic check ---
@app.get("/")
async def read_root():
    return {"message": "Time Management API is running"}