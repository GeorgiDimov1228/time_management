# time_management/app/crud.py
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_
from sqlalchemy.future import select as future_select # If using SQLAlchemy < 2.0 style select with async
from app import models, schemas
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_employee_sync(db: Session, user_id: int): 
    """Synchronous function to get employee by ID."""
    if not db: # Add check for None db session
        return None
    try:
        return db.query(models.Employee).filter(models.Employee.id == user_id).first()
    except Exception as e:
        print(f"Error in get_employee_sync: {e}")
        return None


def get_employee_by_username_sync(db: Session, username: str): 
    """Synchronous function to get employee by username."""
    if not db:
        return None
    try:
        return db.query(models.Employee).filter(models.Employee.username == username).first()
    except Exception as e:
        print(f"Error in get_employee_by_username_sync: {e}")
        return None

def create_employee_sync(db: Session, employee: schemas.EmployeeCreate): 
    """Synchronous function to create an employee."""
    if not db:
        raise ValueError("Database session is required.")
    try:
        if employee.is_admin and not employee.password:
            raise ValueError("Admin users must have a password.")

        hashed_password = pwd_context.hash(employee.password) if employee.password else ""

        db_employee = models.Employee(
            username=employee.username,
            email=employee.email,
            rfid=employee.rfid,
            hashed_password=hashed_password,
            is_admin=employee.is_admin
        )
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        db.rollback() # Rollback on error
        print(f"Error in create_employee_sync: {e}")
        raise # Re-raise the exception after logging/rollback


async def get_employees(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Employee).offset(skip).limit(limit))
    return result.scalars().all()

async def get_employee(db: AsyncSession, user_id: int): 
    result = await db.execute(select(models.Employee).filter(models.Employee.id == user_id))
    return result.scalars().first()

async def get_employee_by_rfid(db: AsyncSession, rfid: str):
    result = await db.execute(select(models.Employee).filter(models.Employee.rfid == rfid))
    return result.scalars().first()

async def get_employee_by_username(db: AsyncSession, username: str): 
    result = await db.execute(select(models.Employee).filter(models.Employee.username == username))
    return result.scalars().first()

async def create_employee(db: AsyncSession, employee: schemas.EmployeeCreate): 
    if employee.is_admin and not employee.password:
        raise ValueError("Admin users must have a password.")

    hashed_password = pwd_context.hash(employee.password) if employee.password else ""

    db_employee = models.Employee(
        username=employee.username,
        email=employee.email,
        rfid=employee.rfid,
        hashed_password=hashed_password,
        is_admin=employee.is_admin
    )
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee


async def update_employee(db: AsyncSession, user_id: int, employee_update: schemas.EmployeeCreate):
    db_employee = await get_employee(db, user_id) 
    if not db_employee: return None
    update_data = employee_update.model_dump(exclude_unset=True)
    if 'password' in update_data and update_data['password']:
        update_data['hashed_password'] = pwd_context.hash(update_data['password'])
        del update_data['password']
    elif 'password' in update_data: del update_data['password']
    for key, value in update_data.items(): setattr(db_employee, key, value)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee

async def delete_employee(db: AsyncSession, user_id: int):
    db_employee = await get_employee(db, user_id) 
    if not db_employee: return None
    await db.delete(db_employee)
    await db.commit()
    return db_employee

async def update_password(db: AsyncSession, user_id: int, current_password: str, new_password: str):
    db_employee = await get_employee(db, user_id) 
    if not db_employee: return None
    if not pwd_context.verify(current_password, db_employee.hashed_password): return False
    db_employee.hashed_password = pwd_context.hash(new_password)
    await db.commit()
    await db.refresh(db_employee)
    return db_employee

async def get_latest_attendance_event(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.AttendanceEvent).filter(models.AttendanceEvent.user_id == user_id).order_by(models.AttendanceEvent.timestamp.desc()).limit(1))
    return result.scalars().first()

async def create_attendance_event(db: AsyncSession, event_data: models.AttendanceEvent):
    db.add(event_data)
    await db.commit()
    await db.refresh(event_data)
    return event_data

async def get_checkin_events(db: AsyncSession):
    result = await db.execute(select(models.AttendanceEvent).filter(models.AttendanceEvent.event_type == "checkin"))
    return result.scalars().all()

async def get_checkout_events(db: AsyncSession):
    result = await db.execute(select(models.AttendanceEvent).filter(models.AttendanceEvent.event_type == "checkout"))
    return result.scalars().all()

async def get_filtered_attendance_events(
    db: AsyncSession,
    start_date: datetime = None,
    end_date: datetime = None,
    event_type: str = None,
    user_id: int = None,
    username: str = None,
    manual: bool = None
):
    """Get attendance events with filters applied"""
    query = select(models.AttendanceEvent).join(models.Employee)
    
    # Build filter conditions
    conditions = []
    
    if start_date:
        conditions.append(models.AttendanceEvent.timestamp >= start_date)
    
    if end_date:
        conditions.append(models.AttendanceEvent.timestamp <= end_date)
    
    if event_type:
        conditions.append(models.AttendanceEvent.event_type == event_type)
    
    if user_id:
        conditions.append(models.AttendanceEvent.user_id == user_id)
    
    if username:
        conditions.append(models.Employee.username == username)
    
    if manual is not None:  # Check if it's explicitly True or False
        conditions.append(models.AttendanceEvent.manual == manual)
    
    # Apply all conditions if any exist
    if conditions:
        query = query.filter(and_(*conditions))
    
    # Order by timestamp descending (newest first)
    query = query.order_by(models.AttendanceEvent.timestamp.desc())
    
    result = await db.execute(query)
    return result.scalars().all()