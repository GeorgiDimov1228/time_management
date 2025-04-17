# from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
# from sqlalchemy.orm import relationship
from datetime import datetime
# from .database import Base

from tortoise import fields
from tortoise.models import Model

class Employee(Model):
    """
    Tortoise ORM Model for Employee.
    """
    id = fields.IntField(pk=True)
    # Ensure unique=True where needed based on your original model
    username = fields.CharField(max_length=100, unique=True, index=True)
    email = fields.CharField(max_length=255, unique=True, index=True, null=True) # Allow null email? Check requirement
    # rfid = fields.CharField(max_length=100, unique=True, index=True)
    rfid = fields.CharField(max_length=100, unique=True, index=True, null=True)
    password = fields.CharField(max_length=255, null=True) # Allow null for non-admins?
    is_admin = fields.BooleanField(default=False)

    # Relationship defined via ReverseRelation in AttendanceEvent
    # attendance_events: fields.ReverseRelation["AttendanceEvent"] # Defined below

    # Tortoise uses Pydantic V1 style for Meta if needed, or often inferred
    class Meta:
        table = "employees" # Explicitly set table name

    def __str__(self):
        # Used by fastapi-admin in dropdowns/representations
        return f"{self.username} (RFID: {self.rfid})"

class AttendanceEvent(Model):
    """
    Tortoise ORM Model for AttendanceEvent.
    """
    id = fields.IntField(pk=True)
    employee: fields.ForeignKeyRelation[Employee] = fields.ForeignKeyField(
        "models.Employee", related_name="attendance_events", description="Employee ID" # related_name enables Employee.attendance_events
    )
    # Tortoise automatically creates employee_id field
    event_type = fields.CharField(max_length=50, index=True)  # "checkin" or "checkout"
    timestamp = fields.DatetimeField(auto_now_add=True) # Automatically set on creation
    manual = fields.BooleanField(default=False)

    # Define reverse relation for accessing from Employee model
    # This is implicitly created by related_name='attendance_events' in ForeignKeyField
    # employee: fields.ReverseRelation["Employee"] # This line isn't strictly needed here

    class Meta:
        table = "attendance_events"
        # Example: ordering = ["-timestamp"] # Default ordering

    def __str__(self):
        return f"{self.event_type} - {self.id}"

# Define reverse relations explicitly if needed for type hinting elsewhere
# Employee.attendance_events = fields.ReverseRelation["models.AttendanceEvent"]
