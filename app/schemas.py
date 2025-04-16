from pydantic import BaseModel, EmailStr, constr, validator
from datetime import datetime
from typing import Optional

# Scan Schemas
# class RFIDScanResponse(BaseModel):
#     employee_id: int
#     username: str
#     last_event: Optional[str] = None
#     last_event_time: Optional[datetime] = None

#     class Config:
#         from_attributes = True
#         orm_mode = True         
#         allow_population_by_field_name = True
#         use_enum_values = True
#         arbitrary_types_allowed = True
#         json_encoders = {
#             datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
#         }
#         schema_extra = {
#             "example": {
#                 "employee_id": 1,
#                 "username": "johndoe",
#                 "last_event": "checkin",
#                 "last_event_time": "2023-10-01T12:00:00Z"
#             }
#         }
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