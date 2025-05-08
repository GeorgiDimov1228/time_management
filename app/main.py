# time_management/app/main.py
import os
import datetime
import asyncio # Import asyncio for potential future use in startup events
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# --- Database Imports ---
# Import sync engine and session for SQLAdmin and initial setup
# Import Base for table creation
# Import AsyncSessionLocal for potential type hinting or future async startup tasks
from app.database import sync_engine, Base, SyncSessionLocal, AsyncSessionLocal
# Alias SyncSessionLocal for easier use in create_default_admin
SessionLocal = SyncSessionLocal

# --- App Component Imports ---
from app import models, crud, schemas
from app.routes import users, attendance, admin
from app.auth import router as auth_router

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

# --- Mount Static Files ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# --- Include API Routers ---
# Note the dependencies used within each router
app.include_router(auth_router, prefix="/api")       
app.include_router(users.router, prefix="/api")       
app.include_router(attendance.router, prefix="/api")
app.include_router(admin.router)  # Admin router with custom UI

# --- Schema Updates ---
def update_schema():
    """Ensure database schema is up to date with model changes."""
    print("Checking for schema updates...")
    
    # Use a synchronous connection for schema updates
    from sqlalchemy import text
    with sync_engine.connect() as conn:
        # Check if notes column exists in attendance_events
        check_query = text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='attendance_events' AND column_name='notes';
        """)
        
        result = conn.execute(check_query)
        exists = result.scalar() is not None
        
        if not exists:
            print("Adding 'notes' column to attendance_events table...")
            add_column_query = text("""
            ALTER TABLE attendance_events 
            ADD COLUMN notes TEXT;
            """)
            conn.execute(add_column_query)
            conn.commit()
            print("Column added successfully.")
        else:
            print("Notes column already exists.")

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
try:
    create_default_admin()
    update_schema()  # Add schema update check
    print("Startup tasks complete.")
except Exception as e:
    print(f"Error during startup tasks: {e}")

# --- Optional: Add root endpoint for basic check ---
@app.get("/")
async def read_root():
    return {"message": "Time Management API is running"}