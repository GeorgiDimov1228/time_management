# app/routes/attendance.py
from fastapi import APIRouter, HTTPException, Depends, Body
# from sqlalchemy.orm import Session # <-- REMOVE
from datetime import datetime, timedelta, timezone
from app import models, schemas, crud, security # Import async crud functions
from typing import List
# from app.database import get_db # <-- REMOVE
import os


# Define cooldown period
ACTION_COOLDOWN_SECONDS = int(os.getenv("ACTION_COOLDOWN_SECONDS", 10))

router = APIRouter(
    tags=["attendance"],
)

# --- Make routes async, remove db dependency, await crud/Tortoise calls ---

@router.post("/scan", response_model=schemas.AttendanceEventResponse)
async def process_rfid_scan( # <-- async def
    scan_data: schemas.RFIDScanRequest,
    # db: Session = Depends(get_db) # <-- REMOVE
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing direct scan request for RFID: {rfid_tag}")

    # 1. Find Employee (use async crud)
    employee = await crud.get_employee_by_rfid(rfid_tag) # <-- await
    if not employee:
        print(f"Employee not found for RFID: {rfid_tag}")
        raise HTTPException(status_code=404, detail="Employee not found")

    # 2. Get Last Event (use async crud)
    latest_event = await crud.get_latest_attendance_event(employee.id) # <-- await

    last_event_type = latest_event.event_type if latest_event else None
    last_event_dt = latest_event.timestamp if latest_event else None # Assuming timestamp is datetime

    # 3. Check Cooldown
    if last_event_dt:
        # Ensure last_event_dt is timezone-aware (Tortoise might handle this depending on config)
        if last_event_dt.tzinfo is None:
             # If Tortoise stores naive datetimes, assume UTC
             last_event_dt = last_event_dt.replace(tzinfo=timezone.utc)

        current_time_utc = datetime.now(timezone.utc)
        time_since_last_event = current_time_utc - last_event_dt
        print(f"Time since last event ('{last_event_type}' at {last_event_dt}): {time_since_last_event}")

        if time_since_last_event.total_seconds() < ACTION_COOLDOWN_SECONDS:
            print(f"Cooldown active for {rfid_tag}. Ignoring scan.")
            raise HTTPException(status_code=429, detail=f"Cooldown active. Try again later. Last event: {last_event_type} at {last_event_dt}")
        else:
            print("Cooldown passed.")
    else:
        print("No previous event found, proceeding.")

    # 4. Determine Next Action
    next_action = "checkout" if last_event_type == "checkin" else "checkin"
    print(f"Determined action for {rfid_tag}: '{next_action}'")

    # 5. Create and Record New Event (use async crud)
    new_event = await crud.create_attendance_event(employee.id, next_action) # <-- await
    print(f"Successfully recorded '{next_action}' for {rfid_tag}")

    return new_event # Return Tortoise model (ensure schema uses from_attributes)


@router.get("/employees/status", response_model=schemas.EmployeeStatusResponse)
async def get_employee_status(rfid: str): # <-- async def, removed db
    # Look up employee by RFID (use async crud)
    employee = await crud.get_employee_by_rfid(rfid) # <-- await
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Get the employee's most recent attendance event (use async crud)
    latest_event = await crud.get_latest_attendance_event(employee.id) # <-- await

    # Determine status based on latest event
    last_event_type = latest_event.event_type if latest_event else None

    # Prepare response data (ensure schema has from_attributes=True)
    return {
        "employee_id": employee.id,
        "username": employee.username,
        "last_event": last_event_type,
        "last_event_time": latest_event.timestamp if latest_event else None
    }

# Note: The separate /checkin and /checkout endpoints might become redundant
# if all scans go through the unified /scan endpoint.
# If you keep them, they also need to be async and use async crud.

@router.post("/checkin", response_model=schemas.AttendanceEventResponse, deprecated=True) # Mark as deprecated?
async def check_in(rfid: str): # <-- async def, removed db
    employee = await crud.get_employee_by_rfid(rfid) # <-- await
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    # Use async crud function to create event
    event = await crud.create_attendance_event(employee.id, "checkin") # <-- await
    return event

@router.get("/checkin", response_model=List[schemas.AttendanceEventResponse], deprecated=True)
async def get_checkins(): # <-- async def, removed db
    # Use Tortoise query directly
    events = await models.AttendanceEvent.filter(event_type="checkin").all() # <-- await
    return events

@router.post("/checkout", response_model=schemas.AttendanceEventResponse, deprecated=True) # Mark as deprecated?
async def check_out(rfid: str): # <-- async def, removed db
    employee = await crud.get_employee_by_rfid(rfid) # <-- await
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    # Use async crud function to create event
    event = await crud.create_attendance_event(employee.id, "checkout") # <-- await
    return event

@router.get("/checkout", response_model=List[schemas.AttendanceEventResponse], deprecated=True)
async def get_checkouts(): # <-- async def, removed db
    # Use Tortoise query directly
    events = await models.AttendanceEvent.filter(event_type="checkout").all() # <-- await
    return events