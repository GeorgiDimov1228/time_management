from pydantic import BaseModel, EmailStr, constr, validator
from datetime import datetime
from typing import Optional

# Employee Schemas
class EmployeeBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None  
    rfid: str

class EmployeeCreate(EmployeeBase):
    password: constr(min_length=8)
    is_admin: bool = False  # Include the flag here
    

class EmployeeResponse(EmployeeBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True



# Attendance Schemas
class AttendanceEventBase(BaseModel):
    user_id: int
    event_type: str  # "checkin" or "checkout"

class AttendanceEventCreate(AttendanceEventBase):
    pass

class AttendanceEventResponse(AttendanceEventBase):
    id: int
    timestamp: datetime
    manual: bool

    class Config:
        from_attributes = True

# password
class PasswordUpdate(BaseModel):
    current_password: constr(min_length=8)
    new_password: constr(min_length=8)