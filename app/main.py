# app/main.py
import os
from contextlib import asynccontextmanager # <-- Import context manager
from fastapi import FastAPI, Request, HTTPException, status
from app import models, crud, schemas # Import Tortoise models, crud, schemas
from app.security import pwd_context
import aioredis



# Import Tortoise ORM config
from app.tortoise_config import TORTOISE_ORM_CONFIG

# --- Tortoise ORM Initialization ---
from tortoise.contrib.fastapi import register_tortoise

# --- FastAdmin Imports ---
from fastapi_admin.app import app as admin_app
from fastapi_admin.resources import Model, Field, ComputeField
from fastapi_admin.widgets import displays, filters, inputs
from fastapi_admin.providers.login import UsernamePasswordProvider # <-- Import login provider
from fastapi.responses import RedirectResponse

# from fastapi_admin.models import AbstractAdmin # May not be needed if using Employee model
# from fastapi_admin.site import Site # Import if configuring site options

@admin_app.get("/", include_in_schema=False)
async def admin_index():
    # Redirect to the list view of the first resource as a default landing page
    return RedirectResponse(url="/admin/employee/list") # Check if '/list' is correct path


# --- Async function to create default admin (Keep this definition) ---
async def create_default_admin_async():
    # Using await to call the async crud function
    admin_user = await crud.get_employee_by_username("admin") # Default username 'admin'
    if not admin_user:
        default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        # Ensure you have a default password set in your .env or environment
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not default_password:
             print("ERROR: DEFAULT_ADMIN_PASSWORD environment variable not set. Cannot create default admin.")
             return # Or raise an error

        print(f"Attempting to create default admin user '{default_username}'...")
        admin_data = schemas.EmployeeCreate(
            username=default_username,
            email=default_email,
            rfid="ADMIN_RFID_001", # Assign a default/placeholder RFID
            password=default_password,
            is_admin=True
        )
        try:
            # Using await to call the async crud function
            created_user = await crud.create_employee(employee=admin_data)
            if created_user:
                 print(f"Default admin user '{created_user.username}' created successfully.")
            else:
                 print(f"Failed to create default admin user '{default_username}'. It might already exist or there was a DB issue.")
        except Exception as e:
            print(f"Error during default admin creation: {e}")
    else:
        print(f"Admin user '{admin_user.username}' already exists.")

# --- Define Custom ComputeField (Keep this definition) ---
class AttendanceEventsCountField(ComputeField):
    async def get_value(self, request: Request, obj: dict):
        employee_instance = await models.Employee.get_or_none(id=obj.get("id"))
        if employee_instance:
            count = await employee_instance.attendance_events.all().count()
            return count
        return 0


# --- !!! CORRECTED Custom Login Provider !!! ---
class CustomLoginProvider(UsernamePasswordProvider):
    async def authenticate(self, username: str, password: str):
        admin = await models.Employee.get_or_none(username=username)

        # If user not found OR password verification fails, return None
        if not admin or not pwd_context.verify(password, admin.hashed_password):
             # Let the fastapi-admin framework handle generating the user-facing error
             return None # <-- Return None on failure

        # Only return the admin object if authentication succeeds
        return admin

# --- !!! END: Corrected Custom Login Provider !!! ---

# --- Lifespan Function (New Way) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run before the application starts (startup) ---
    print("Lifespan: Initializing Tortoise and Admin...")

    # NOTE: register_tortoise handles its own lifespan for DB connections.
    # We configure the admin app here after connections are expected to be ready.

    admin_secret = os.getenv("ADMIN_SECRET", "please_change_this_secret_in_prod")
    redis_url = os.getenv("REDIS_URL") # Get Redis URL from env

    # Configure the login provider using Employee model
    login_provider = UsernamePasswordProvider(
        admin_model=models.Employee, # Use your Employee model for admin login
        login_logo_url="https://preview.tabler.io/static/logo.svg" # Optional logo
    )

    # --- Create Redis Pool ---
    redis_pool = None
    if redis_url:
        try:
            # Use from_url for simplicity if aioredis v2+
            redis_pool = await aioredis.from_url(redis_url, encoding="utf8")
            print("Lifespan: Redis pool created.")
        except Exception as e:
            print(f"Lifespan: Failed to create Redis pool: {e}")
            # Decide if Redis failure should prevent startup? Maybe not.
            redis_pool = None # Ensure it's None if creation failed
    else:
        print("Lifespan: REDIS_URL not set, skipping Redis pool creation.")



    # Configure the admin app
    # redis = await aioredis.create_redis_pool("redis://localhost", encoding="utf8")
    await admin_app.configure(
        logo_url="https://preview.tabler.io/static/logo-white.svg",
        template_folders=[os.path.join(os.path.dirname(__file__), "templates")], # Optional
        providers=[login_provider],
        redis=redis_pool,
        # redis=os.getenv("REDIS_URL", "please_change_this_secret_in_prod"), # Optional
        # admin_secret=admin_secret
    )

    # Create default admin user (needs DB connection from register_tortoise)
    print("Lifespan: Creating default admin user (if needed)...")
    # await create_default_admin_async()

    print("Lifespan: Startup complete.")
    yield
    # --- Code to run after the application shuts down ---
    print("Lifespan: Application shutting down...")
    # Tortoise connections are closed automatically by register_tortoise


# --- Your FastAPI app instance (with lifespan) ---
app = FastAPI(title="Time Management API - Tortoise", lifespan=lifespan) # <-- Use lifespan here

# --- Register Tortoise ORM ---
# Needs to be setup so the lifespan function can use the DB
register_tortoise(
    app,
    config=TORTOISE_ORM_CONFIG,
    generate_schemas=True, # Creates tables if they don't exist (careful in prod)
    add_exception_handlers=True, # Adds Tortoise exception handlers
)

# --- FastAdmin Resources (Keep these definitions) ---
@admin_app.register
class EmployeeResource(Model):
    label = "Employee"
    model = models.Employee
    icon = "fas fa-user"
    page_pre_title = "employee list"
    page_title = "Employee model"
    fields = [
        "id", "username", "email", "rfid", "is_admin",
        AttendanceEventsCountField(name="attendance_events_count", label="Events Count"),
    ]
    search_fields = ("username", "rfid", "email")
    filters = [
        filters.Search(name="username", label="Username", search_mode="contains"),
        filters.Boolean(name="is_admin", label="Is Admin"),
    ]

@admin_app.register
class AttendanceEventResource(Model):
    label = "Attendance Event"
    model = models.AttendanceEvent
    icon = "fas fa-clock"
    page_pre_title = "event list"
    page_title = "Attendance Event model"
    fields = [
        "id",
        # Field(name="employee__username", label="Username"), # Revisit this if default display isn't right
        "employee", # Display ForeignKey directly first
        "event_type",
        "timestamp",
        "manual",
    ]
    filters = [
        filters.ForeignKey(model=models.Employee, name="employee", label="Employee"),
        filters.Input(name="event_type", label="Event Type"),
        filters.Boolean(name="manual", label="Manual"),
    ]
    # Adjust search based on direct FK field or computed field if needed
    search_fields = ("employee__username", "event_type") # Might need adjustment

# --- Mount the admin app ---
app.mount("/admin", admin_app)

# --- Include your API Routers ---
from app.routes import users, attendance
from app.auth import router as auth_router

app.include_router(auth_router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")

