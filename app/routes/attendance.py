from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app import models, schemas, database, crud
from typing import List
from app.database import get_db



router = APIRouter(
    tags=["attendance"],
)


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
