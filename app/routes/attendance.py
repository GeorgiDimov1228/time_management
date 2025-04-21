# time_management/app/routes/attendance.py
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession # Use AsyncSession
from datetime import datetime, timedelta, timezone
from app import models, schemas, crud, security
from app.database import get_async_db # Use async dependency
from typing import List
import os

ACTION_COOLDOWN_SECONDS = int(os.getenv("ACTION_COOLDOWN_SECONDS", 10))

router = APIRouter(
    tags=["attendance"],
)

@router.post("/scan", response_model=schemas.AttendanceEventResponse)
async def process_rfid_scan( # Make async
    scan_data: schemas.RFIDScanRequest,
    db: AsyncSession = Depends(get_async_db), # Use async db
    # Use the async version of get_current_authenticated_user (defined in step 5)
    current_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing direct scan request for RFID: {rfid_tag} by user: {current_user.username}")

    # Use await with async CRUD functions
    employee = await crud.get_employee_by_rfid(db, rfid_tag)
    if not employee:
        print(f"Employee not found for RFID: {rfid_tag}")
        raise HTTPException(status_code=404, detail="Employee not found")

    latest_event = await crud.get_latest_attendance_event(db, employee.id)

    last_event_type = latest_event.event_type if latest_event else None
    last_event_dt = latest_event.timestamp if latest_event else None

    if last_event_dt:
        if last_event_dt.tzinfo is None:
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

    next_action = "checkout" if last_event_type == "checkin" else "checkin"
    print(f"Determined action for {rfid_tag}: '{next_action}'")

    new_event_data = models.AttendanceEvent(
        user_id=employee.id,
        event_type=next_action,
        timestamp=datetime.now(timezone.utc),
        manual=False
    )
    # Use await with async CRUD function
    new_event = await crud.create_attendance_event(db, new_event_data)
    print(f"Successfully recorded '{next_action}' for {rfid_tag}")

    return new_event


@router.get("/employees/status", response_model=schemas.EmployeeStatusResponse)
async def get_employee_status(rfid: str,
                              db: AsyncSession = Depends(get_async_db),
                              authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
): # Make async
    # Use await with async CRUD functions
    employee = await crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    latest_event = await crud.get_latest_attendance_event(db, employee.id)

    last_event_type = latest_event.event_type if latest_event else None

    return {
        "employee_id": employee.id,
        "username": employee.username,
        "last_event": last_event_type,
        "last_event_time": latest_event.timestamp if latest_event else None
    }

@router.post("/checkin", response_model=schemas.AttendanceEventResponse)
async def check_in( # Make async
    rfid: str,
    db: AsyncSession = Depends(get_async_db), # Use async db
    # Use the async version of get_current_admin_user (defined in step 5)
    current_admin: models.Employee = Depends(security.get_current_admin_user_async)
):
    # Use await with async CRUD functions
    employee = await crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    print(f"Admin '{current_admin.username}' manually checking in RFID: {rfid}")

    event_data = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkin",
        timestamp=datetime.now(timezone.utc),
        manual=True
    )
    # Use await with async CRUD function
    event = await crud.create_attendance_event(db, event_data)
    return event

@router.get("/checkin", response_model=List[schemas.AttendanceEventResponse])
async def get_checkins(db: AsyncSession = Depends(get_async_db), authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
): # Make async
     # Use await with async CRUD function
    events = await crud.get_checkin_events(db)
    return events


@router.post("/checkout", response_model=schemas.AttendanceEventResponse)
async def check_out( # Make async
    rfid: str,
    db: AsyncSession = Depends(get_async_db), # Use async db
     # Use the async version of get_current_admin_user (defined in step 5)
    current_admin: models.Employee = Depends(security.get_current_admin_user_async)
):
    # Use await with async CRUD functions
    employee = await crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    print(f"Admin '{current_admin.username}' manually checking out RFID: {rfid}")

    event_data = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkout",
        timestamp=datetime.now(timezone.utc),
        manual=True
    )
    # Use await with async CRUD function
    event = await crud.create_attendance_event(db, event_data)
    return event

@router.get("/checkout", response_model=List[schemas.AttendanceEventResponse])
async def get_checkouts(db: AsyncSession = Depends(get_async_db), authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
): # Make async
    # Use await with async CRUD function
    events = await crud.get_checkout_events(db)
    return events