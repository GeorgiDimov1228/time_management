from fastapi import FastAPI
from app.database import engine, Base
from app import models, crud, schemas
from app.routes import users, attendance
from app.auth import router as auth_router  # Import the router object
import os
from app.database import SessionLocal




# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Time Management API")

# Include routers
# Include routers with an '/api' prefix
app.include_router(auth_router, prefix="/api")  # Token endpoint at /token
app.include_router(users.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")


# Create a default admin user if none exists
def create_default_admin():
    db = SessionLocal()
    try:
        admin_user = crud.get_employee_by_username(db, "admin")
        if not admin_user:
            default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
            default_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
            default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminpassword")
            # Create an instance of EmployeeCreate using keyword arguments
            admin_data = schemas.EmployeeCreate(
                username=default_username,
                email=default_email,
                rfid="DEFAULT_ADMIN_RFID",
                password=default_password,
                is_admin=True
            )
            crud.create_employee(db, admin_data)
            print("Default admin user created.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

# Call the function on startup
create_default_admin()