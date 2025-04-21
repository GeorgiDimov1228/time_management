from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    rfid = Column(String, unique=True, index=True)
    hashed_password = Column(String)  # For admin login
    is_admin = Column(Boolean, default=False)  # New field

    attendance_events = relationship("AttendanceEvent", back_populates="employee")

    def __str__(self):
        # Return a user-friendly string representation
        # You can customize this, e.g., return just self.username
        return f"{self.username} (RFID: {self.rfid})" 

class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    event_type = Column(String, index=True)  # "checkin" or "checkout"
    # timestamp = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    manual = Column(Boolean, default=True)

    employee = relationship("Employee", back_populates="attendance_events")
