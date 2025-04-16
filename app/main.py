from fastapi import FastAPI
from app.database import engine, Base, SessionLocal # Added SessionLocal
from app import models, crud, schemas
from app.routes import users, attendance # Removed projects if not used
from app.auth import router as auth_router
import os
import datetime 

# --- SQLAdmin Imports ---
from sqladmin import Admin, ModelView
from app.database import engine # Make sure engine is imported

# --- End SQLAdmin Imports ---


# Create database tables if they don't exist
# Base.metadata.create_all(bind=engine) # SQLAdmin might handle this, or keep it

app = FastAPI(title="Time Management API")

# --- SQLAdmin Setup ---

# Define Admin Views for your models
class EmployeeAdmin(ModelView, model=models.Employee):
    # Columns to display in the list view
    column_list = [models.Employee.id, models.Employee.username, models.Employee.email, models.Employee.rfid, models.Employee.is_admin]
    column_labels = {
        models.Employee.id: "Employee ID", # Example: Label for own column
        models.Employee.username: 'Username',
        models.Employee.email: 'Email', 
        models.Employee.rfid: 'RFID',
        models.Employee.is_admin: 'Admin',

        
    }
    # Columns searchable in the list view
    column_searchable_list = [models.Employee.username, models.Employee.rfid, models.Employee.email]
    # Columns sortable in the list view
    column_sortable_list = [models.Employee.id, models.Employee.username, models.Employee.is_admin]
    # Columns to exclude from the edit/create forms (hashed_password managed elsewhere)
    form_excluded_columns = [models.Employee.hashed_password, models.Employee.attendance_events]
    # Optional: Define which columns are visible/editable in the create/edit forms
    # form_columns = [models.Employee.username, models.Employee.email, models.Employee.rfid, models.Employee.is_admin]
    column_filters = [models.Employee.username, models.Employee.rfid, models.Employee.email] # Keep relationship here for filtering by employee
    name = "Employee"
    name_plural = "Employees"
    icon = "fa-solid fa-user" # Example icon (requires FontAwesome setup if not default)

class AttendanceEventAdmin(ModelView, model=models.AttendanceEvent):
    column_list = [
        models.AttendanceEvent.id,
        'employee.username', # CORRECTED: Use string notation
        models.AttendanceEvent.event_type,
        models.AttendanceEvent.timestamp,
        models.AttendanceEvent.manual
    ]
    column_labels = {
        models.AttendanceEvent.id: "Event ID", # Example: Label for own column
        'employee.username': 'Username', # Label for the related column
        models.AttendanceEvent.event_type: 'Event Type',
        models.AttendanceEvent.timestamp: 'Timestamp',
        models.AttendanceEvent.manual: 'Manual Entry'

    }
    # Format timestamp for the LIST view (hide microseconds)
    column_formatters = {
         models.AttendanceEvent.timestamp:
         lambda m, a: getattr(m, a).strftime("%Y-%m-%d %H:%M:%S") if getattr(m, a) else ""
    }
    # --- Add column_formatters_detail to format timestamp display on DETAIL view ---
    column_formatters_detail = {
        models.AttendanceEvent.timestamp:
        # Example: Show full timestamp with microseconds on detail page
        lambda m, a: getattr(m, a).strftime("%Y-%m-%d %H:%M:%S") if getattr(m, a) else ""
    }
    column_sortable_list = [models.AttendanceEvent.id, models.AttendanceEvent.timestamp, models.AttendanceEvent.event_type, 'employee.username', models.AttendanceEvent.manual] # CORRECTED: Use string notation
    column_searchable_list = [
        models.AttendanceEvent.event_type,
        'employee.username' # CORRECTED: Use string notation
    ]

    # Use STRING notation for related fields in lists
    column_details_list = [ # Columns shown in the detail view
         models.AttendanceEvent.id,
         'employee.username', # CORRECTED: Use string notation
         models.AttendanceEvent.event_type,
         models.AttendanceEvent.timestamp,
         models.AttendanceEvent.manual
    ]
    # Filtering usually works on the relationship object itself or specific columns
    column_filters = [models.AttendanceEvent.event_type, models.AttendanceEvent.manual, models.AttendanceEvent.employee] # Keep relationship here for filtering by employee
    name = "Attendance Event"
    name_plural = "Attendance Events"
    icon = "fa-solid fa-clock"

# Create Admin instance
# Note: Authentication is NOT configured here for simplicity.
# See SQLAdmin docs for adding authentication backends.
admin = Admin(app=app, engine=engine) # No AuthenticationBackend provided initially

# Register Admin Views
admin.add_view(EmployeeAdmin)
admin.add_view(AttendanceEventAdmin)

# --- End SQLAdmin Setup ---


# Include API routers (AFTER Admin setup if admin uses same path prefix potentially)
app.include_router(auth_router, prefix="/api") # Token endpoint at /api/token
app.include_router(users.router, prefix="/api") # Prefixed with /api/users
app.include_router(attendance.router, prefix="/api") # Prefixed with /api/attendance


# Create a default admin user if none exists (Keep this logic)
def create_default_admin():
    # Use SessionLocal for database operations outside requests
    db = SessionLocal()
    try:
        admin_user = crud.get_employee_by_username(db, "admin")
        if not admin_user:
            default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
            default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminpassword")

            admin_data = schemas.EmployeeCreate(
                username=default_username,
                email=default_email,
                rfid="DEFAULT_ADMIN_RFID", # Assign a default RFID if needed
                password=default_password,
                is_admin=True
            )
            print("Attempting to create default admin user...")
            created_user = crud.create_employee(db=db, employee=admin_data)
            if created_user:
                 print(f"Default admin user '{created_user.username}' created.")
            else:
                 print("Failed to create default admin user.") # Should not happen unless DB error
        else:
            print("Admin user already exists.")
    except Exception as e:
        print(f"Error during default admin creation: {e}")
    finally:
        db.close()

# Call the function on startup
# Consider running this in an explicit startup event if needed
# @app.on_event("startup")
# async def startup_event():
#     create_default_admin()
create_default_admin() # Call directly for now
