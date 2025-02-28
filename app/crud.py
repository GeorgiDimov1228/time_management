from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Employee).offset(skip).limit(limit).all()

def get_employee(db: Session, user_id: int):
    return db.query(models.Employee).filter(models.Employee.id == user_id).first()

def get_employee_by_rfid(db: Session, rfid: str):
    return db.query(models.Employee).filter(models.Employee.rfid == rfid).first()

def get_employee_by_username(db: Session, username: str):
    return db.query(models.Employee).filter(models.Employee.username == username).first()

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    # Enforce that admin users must have a password
    if employee.is_admin and not employee.password:
        raise ValueError("Admin users must have a password.")

    # If a password is provided, hash it; otherwise, use an empty string (or you could store None)
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

def update_employee(db: Session, user_id: int, employee: schemas.EmployeeCreate):
    db_employee = get_employee(db, user_id)
    if not db_employee:
        return None
    
    db_employee.username = employee.username
    db_employee.email = employee.email
    db_employee.rfid = employee.rfid
    
    # Only update the password if one is provided.
    if employee.password:
        db_employee.hashed_password = pwd_context.hash(employee.password)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, user_id: int):
    db_employee = get_employee(db, user_id)
    if not db_employee:
        return None
    db.delete(db_employee)
    db.commit()
    return db_employee

def update_password(db: Session, user_id: int, current_password: str, new_password: str):
    db_employee = get_employee(db, user_id)
    if not db_employee:
         return None  # User not found
    if not pwd_context.verify(current_password, db_employee.hashed_password):
         return False  # Current password does not match
    db_employee.hashed_password = pwd_context.hash(new_password)
    db.commit()
    db.refresh(db_employee)
    return db_employee
