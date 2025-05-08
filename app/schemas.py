from pydantic import BaseModel, EmailStr, constr, validator
from datetime import datetime
from typing import Optional

# Scan Schemas
class RFIDScanRequest(BaseModel):
    rfid: str

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


class EmployeeStatusResponse(BaseModel):
    employee_id: int
    username: str
    last_event: Optional[str] = None
    last_event_time: Optional[datetime] = None

    class Config:
        from_attributes = True