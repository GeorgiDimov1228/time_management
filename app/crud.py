# app/crud.py
# No db session needed as argument anymore, import models directly
from app import models, schemas
from passlib.context import CryptContext
# Tortoise exceptions might be needed
from tortoise.exceptions import DoesNotExist, IntegrityError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Note: Functions are now async!

async def get_employees(skip: int = 0, limit: int = 100):
    return await models.Employee.all().offset(skip).limit(limit)

async def get_employee(user_id: int):
    try:
        # Use .get() which raises DoesNotExist if not found
        return await models.Employee.get(id=user_id)
    except DoesNotExist:
        return None

async def get_employee_by_rfid(rfid: str):
    # Use .filter().first() which returns None if not found
    return await models.Employee.filter(rfid=rfid).first()

async def get_employee_by_username(username: str):
    return await models.Employee.filter(username=username).first()

async def create_employee(employee: schemas.EmployeeCreate):
    if employee.is_admin and not employee.password:
        raise ValueError("Admin users must have a password.")

    hashed_password = pwd_context.hash(employee.password) if employee.password else None # Store None if no password?

    try:
        # Use Model.create()
        db_employee = await models.Employee.create(
            username=employee.username,
            email=employee.email,
            rfid=employee.rfid,
            password=hashed_password,
            is_admin=employee.is_admin
        )
        return db_employee
    except IntegrityError as e:
        # Handle potential unique constraint violations (e.g., duplicate username/email/rfid)
        print(f"Error creating employee: {e}")
        # You might want to raise a specific HTTP exception here
        return None # Or re-raise a custom exception

async def update_employee(user_id: int, employee: schemas.EmployeeCreate):
    db_employee = await get_employee(user_id)
    if not db_employee:
        return None

    update_data = employee.model_dump(exclude_unset=True) # Get only fields present in input

    # Don't update password here unless explicitly intended by the schema/logic
    if 'password' in update_data:
        del update_data['password'] # Remove password from general update

    # Update fields
    db_employee.username = update_data.get('username', db_employee.username)
    db_employee.email = update_data.get('email', db_employee.email)
    db_employee.rfid = update_data.get('rfid', db_employee.rfid)
    # You might need to update is_admin too if part of EmployeeCreate schema for updates

    await db_employee.save() # Use obj.save()
    return db_employee

async def delete_employee(user_id: int):
    db_employee = await get_employee(user_id)
    if not db_employee:
        return None
    await db_employee.delete() # Use obj.delete()
    return db_employee # Return the deleted object (or True?)

async def update_password(user_id: int, current_password: str, new_password: str):
    db_employee = await get_employee(user_id)
    if not db_employee:
         return None  # User not found

    # Handle cases where non-admins might not have a password set
    if not db_employee.hashed_password:
        if current_password: # Trying to change from no password using a 'current' password
             return False # Incorrect current password (as there is none)
        # Allow setting initial password if current_password is empty? Check logic.

    elif not pwd_context.verify(current_password, db_employee.hashed_password):
         return False  # Current password does not match

    db_employee.hashed_password = pwd_context.hash(new_password)
    await db_employee.save()
    return db_employee

# --- Add CRUD for AttendanceEvent if needed, e.g., getting last event ---
async def get_latest_attendance_event(employee_id: int):
     return await models.AttendanceEvent.filter(employee_id=employee_id).order_by("-timestamp").first()

async def create_attendance_event(employee_id: int, event_type: str, manual: bool = False):
    event = await models.AttendanceEvent.create(
        employee_id=employee_id,
        event_type=event_type,
        manual=manual
        # timestamp is auto_now_add
    )
    return event