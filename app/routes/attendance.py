from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app import models, schemas, database, crud
from typing import List
from app.database import get_db
import os

# Define cooldown period (consider making this configurable via environment variable)
ACTION_COOLDOWN_SECONDS = int(os.getenv("ACTION_COOLDOWN_SECONDS", 10))

router = APIRouter(
    tags=["attendance"],
)


# Add this new route to app/routes/attendance.py
@router.post("/scan", response_model=schemas.AttendanceEventResponse) # Or a custom response
def process_rfid_scan(
    scan_data: schemas.RFIDScanRequest, # Use the new schema
    db: Session = Depends(get_db)
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing direct scan request for RFID: {rfid_tag}")

    # 1. Find Employee
    employee = crud.get_employee_by_rfid(db, rfid_tag)
    if not employee:
        print(f"Employee not found for RFID: {rfid_tag}")
        raise HTTPException(status_code=404, detail="Employee not found")

    # 2. Get Last Event (similar to /employees/status route)
    latest_event = db.query(models.AttendanceEvent)\
        .filter(models.AttendanceEvent.user_id == employee.id)\
        .order_by(models.AttendanceEvent.timestamp.desc())\
        .first()

    last_event_type = latest_event.event_type if latest_event else None
    last_event_dt = latest_event.timestamp if latest_event else None

    # 3. Check Cooldown (logic from bridge.py)
    if last_event_dt:
        # Ensure last_event_dt is timezone-aware (assuming stored as UTC)
        if last_event_dt.tzinfo is None:
            last_event_dt = last_event_dt.replace(tzinfo=timezone.utc)

        current_time_utc = datetime.now(timezone.utc)
        time_since_last_event = current_time_utc - last_event_dt
        print(f"Time since last event ('{last_event_type}' at {last_event_dt}): {time_since_last_event}")

        if time_since_last_event.total_seconds() < ACTION_COOLDOWN_SECONDS:
            print(f"Cooldown active for {rfid_tag}. Ignoring scan.")
            # You might return a specific status or message indicating cooldown active
            # For now, raise an exception, but a 200 OK with a specific body might be better UX
            raise HTTPException(status_code=429, detail=f"Cooldown active. Try again later. Last event: {last_event_type} at {last_event_dt}")
        else:
            print("Cooldown passed.")
    else:
        print("No previous event found, proceeding.")

    # 4. Determine Next Action
    next_action = "checkout" if last_event_type == "checkin" else "checkin"
    print(f"Determined action for {rfid_tag}: '{next_action}'")

    # 5. Create and Record New Event (similar to /checkin & /checkout routes)
    new_event = models.AttendanceEvent(
        user_id=employee.id,
        event_type=next_action,
        timestamp=datetime.now(timezone.utc), # Store UTC time
        manual=False # Scan is not manual
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    print(f"Successfully recorded '{next_action}' for {rfid_tag}")

    # Return the newly created event details
    return new_event


@router.get("/employees/status", response_model=schemas.EmployeeStatusResponse)
def get_employee_status(rfid: str, db: Session = Depends(get_db)):
    # Look up employee by RFID
    employee = crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get the employee's most recent attendance event
    latest_event = db.query(models.AttendanceEvent)\
        .filter(models.AttendanceEvent.user_id == employee.id)\
        .order_by(models.AttendanceEvent.timestamp.desc())\
        .first()
    
    # Determine status based on latest event
    last_event_type = latest_event.event_type if latest_event else None
    
    return {
        "employee_id": employee.id,
        "username": employee.username,
        "last_event": last_event_type,
        "last_event_time": latest_event.timestamp if latest_event else None
    }

@router.post("/checkin", response_model=schemas.AttendanceEventResponse)
def check_in(rfid: str, db: Session = Depends(get_db)):
    # Look up employee by RFID
    employee = crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    event = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkin",
        timestamp=datetime.utcnow(),
        manual=False
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("/checkin", response_model=List[schemas.AttendanceEventResponse])
def get_checkins(db: Session = Depends(get_db)):
    events = db.query(models.AttendanceEvent).filter(models.AttendanceEvent.event_type == "checkin").all()
    return events

@router.post("/checkout", response_model=schemas.AttendanceEventResponse)
def check_out(rfid: str, db: Session = Depends(get_db)):
    # Look up employee by RFID
    employee = crud.get_employee_by_rfid(db, rfid)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    event = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkout",
        timestamp=datetime.utcnow(),
        manual=False
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("/checkout", response_model=List[schemas.AttendanceEventResponse])
def get_checkouts(db: Session = Depends(get_db)):
    events = db.query(models.AttendanceEvent).filter(models.AttendanceEvent.event_type == "checkout").all()
    return events
