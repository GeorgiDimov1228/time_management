# time_management/app/routes/attendance.py
from fastapi import APIRouter, HTTPException, Depends, Body, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession # Use AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
from app import models, schemas, crud, security
from app.database import get_async_db # Use async dependency
from typing import List, Optional, Dict, Any
import os
import csv
import io
from fastapi.responses import StreamingResponse

ACTION_COOLDOWN_SECONDS = int(os.getenv("ACTION_COOLDOWN_SECONDS", 10))

router = APIRouter(
    tags=["attendance"],
)

# Helper function to create a CSV StreamingResponse
def create_csv_response(data: List[List[str]], filename: str) -> StreamingResponse:
    """Helper function to create a CSV streaming response"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write data
    for row in data:
        writer.writerow(row)
    
    # Reset the pointer to the beginning of the StringIO object
    output.seek(0)
    
    # Return the CSV as a downloadable file
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/scan", response_model=schemas.AttendanceEventResponse)
async def process_rfid_scan( 
    scan_data: schemas.RFIDScanRequest,
    db: AsyncSession = Depends(get_async_db),
    # Use the async version of get_current_authenticated_user (defined in step 5)
    current_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing direct scan request for RFID: {rfid_tag} by user: {current_user.username}")


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
    new_event = await crud.create_attendance_event(db, new_event_data)
    print(f"Successfully recorded '{next_action}' for {rfid_tag}")

    return new_event


@router.post("/checkin-scan", response_model=schemas.AttendanceEventResponse)
async def process_checkin_scan( 
    scan_data: schemas.RFIDScanRequest,
    db: AsyncSession = Depends(get_async_db),
    # Use the async version of get_current_authenticated_user (defined in step 5)
    current_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing direct scan request for RFID: {rfid_tag} by user: {current_user.username}")

    employee = await crud.get_employee_by_rfid(db, rfid_tag)
    if not employee:
        print(f"Employee not found for RFID: {rfid_tag}")
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check cooldown regardless of event type
    latest_event = await crud.get_latest_attendance_event(db, employee.id)
    last_event_dt = latest_event.timestamp if latest_event else None

    if last_event_dt:
        if last_event_dt.tzinfo is None:
            last_event_dt = last_event_dt.replace(tzinfo=timezone.utc)

        current_time_utc = datetime.now(timezone.utc)
        time_since_last_event = current_time_utc - last_event_dt
        print(f"Time since last event at {last_event_dt}: {time_since_last_event}")

        if time_since_last_event.total_seconds() < ACTION_COOLDOWN_SECONDS:
            print(f"Cooldown active for {rfid_tag}. Ignoring scan.")
            raise HTTPException(
                status_code=429, 
                detail=f"Cooldown active. Try again later. Last event was at {last_event_dt}"
            )
        else:
            print("Cooldown passed.")
    else:
        print("No previous event found, proceeding.")

    # Always create a check-in event
    new_event_data = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkin",
        timestamp=datetime.now(timezone.utc),
        manual=False
    )
    new_event = await crud.create_attendance_event(db, new_event_data)
    print(f"Successfully recorded check-in for {rfid_tag}")

    return new_event


@router.post("/checkout-scan", response_model=schemas.AttendanceEventResponse)
async def process_checkout_scan( 
    scan_data: schemas.RFIDScanRequest,
    db: AsyncSession = Depends(get_async_db),
    # Use the async version of get_current_authenticated_user (defined in step 5)
    current_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
    rfid_tag = scan_data.rfid.strip()
    if not rfid_tag:
        raise HTTPException(status_code=400, detail="RFID tag cannot be empty")

    print(f"\nProcessing check-out scan request for RFID: {rfid_tag} by user: {current_user.username}")

    employee = await crud.get_employee_by_rfid(db, rfid_tag)
    if not employee:
        print(f"Employee not found for RFID: {rfid_tag}")
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check cooldown regardless of event type
    latest_event = await crud.get_latest_attendance_event(db, employee.id)
    last_event_dt = latest_event.timestamp if latest_event else None

    if last_event_dt:
        if last_event_dt.tzinfo is None:
            last_event_dt = last_event_dt.replace(tzinfo=timezone.utc)

        current_time_utc = datetime.now(timezone.utc)
        time_since_last_event = current_time_utc - last_event_dt
        print(f"Time since last event at {last_event_dt}: {time_since_last_event}")

        if time_since_last_event.total_seconds() < ACTION_COOLDOWN_SECONDS:
            print(f"Cooldown active for {rfid_tag}. Ignoring scan.")
            raise HTTPException(
                status_code=429, 
                detail=f"Cooldown active. Try again later. Last event was at {last_event_dt}"
            )
        else:
            print("Cooldown passed.")
    else:
        print("No previous event found, proceeding.")

    # Always create a check-out event
    new_event_data = models.AttendanceEvent(
        user_id=employee.id,
        event_type="checkout",
        timestamp=datetime.now(timezone.utc),
        manual=False
    )
    new_event = await crud.create_attendance_event(db, new_event_data)
    print(f"Successfully recorded check-out for {rfid_tag}")

    return new_event


@router.get("/employees/status", response_model=schemas.EmployeeStatusResponse)
async def get_employee_status(rfid: str,
                              db: AsyncSession = Depends(get_async_db),
                              authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
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
async def check_in( 
    rfid: str,
    db: AsyncSession = Depends(get_async_db), 
    current_admin: models.Employee = Depends(security.get_current_admin_user_async)
):
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
    event = await crud.create_attendance_event(db, event_data)
    return event

@router.get("/checkin", response_model=List[schemas.AttendanceEventResponse])
async def get_checkins(db: AsyncSession = Depends(get_async_db), authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
): 
    events = await crud.get_checkin_events(db)
    return events


@router.post("/checkout", response_model=schemas.AttendanceEventResponse)
async def check_out( 
    rfid: str,
    db: AsyncSession = Depends(get_async_db), 
    current_admin: models.Employee = Depends(security.get_current_admin_user_async)
):
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

    event = await crud.create_attendance_event(db, event_data)
    return event

@router.get("/checkout", response_model=List[schemas.AttendanceEventResponse])
async def get_checkouts(db: AsyncSession = Depends(get_async_db), authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
): 
    events = await crud.get_checkout_events(db)
    return events

@router.get("/filtered", response_model=List[schemas.AttendanceEventResponse])
async def get_filtered_attendance(
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (checkin/checkout)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    manual: Optional[bool] = Query(None, description="Filter by manual flag (true/false)"),
    db: AsyncSession = Depends(get_async_db),
    authenticated_user: models.Employee = Depends(security.get_current_authenticated_user_async)
):
    """Get attendance events with filters applied"""
    events = await crud.get_filtered_attendance_events(
        db,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        user_id=user_id,
        username=username,
        manual=manual
    )
    return events

@router.get("/export/csv", response_class=StreamingResponse)
async def export_attendance_csv(
    request: Request,
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (checkin/checkout)"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    manual: Optional[bool] = Query(None, description="Filter by manual flag (true/false)"),
    db: AsyncSession = Depends(get_async_db),
    authenticated_user: models.Employee = Depends(security.get_admin_from_cookie)
):
    """Export filtered attendance events as CSV"""
    # Get filtered events
    events = await crud.get_filtered_attendance_events(
        db,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        user_id=user_id,
        username=username,
        manual=manual
    )
    
    # Get all employees
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    
    # Prepare employee statistics
    employee_data = {}
    for employee in employees:
        employee_data[employee.id] = {
            "username": employee.username,
            "rfid": employee.rfid,
            "events": [],
            "total_days": 0,
            "total_hours": 0
        }
    
    # Calculate employee statistics
    calculate_employee_statistics(events, employee_data)
    
    # Prepare CSV data with two sections
    csv_data = [
        # First section: Summary with Days Present and Total Hours
        ['Employee Summary'],
        ['Employee Name', 'Days Present', 'Total Hours'],
    ]
    
    # Add summary rows for each employee
    for emp_id, data in employee_data.items():
        # Only include employees with records in the filtered period
        if data["events"]:
            csv_data.append([
                data["username"],
                data["total_days"],
                f"{data['total_hours']:.2f}"
            ])
    
    # Add separator between sections
    csv_data.append([])
    csv_data.append(['Detailed Attendance Records'])
    
    # Add headers for detailed records
    csv_data.append(['Employee Name', 'Event Type', 'Timestamp'])
    
    # Add detailed rows sorted by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)
    for event in sorted_events:
        csv_data.append([
            event.employee.username,
            event.event_type,
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ])
    
    # Generate filename with current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_export_{timestamp}.csv"
    
    # Return CSV response
    return create_csv_response(csv_data, filename)

@router.get("/admin/report", response_class=StreamingResponse)
async def admin_attendance_report(
    request: Request,
    start_date: datetime = Query(..., description="Report start date (ISO format, required)"),
    end_date: datetime = Query(..., description="Report end date (ISO format, required)"),
    username: Optional[str] = Query(None, description="Filter by employee username"),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(security.get_admin_from_cookie)
):
    """
    Generate a comprehensive attendance report for admins.
    Requires admin privileges.
    """
    # Get all employees
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    
    # Get all attendance events in date range with optional employee filter
    events = await crud.get_filtered_attendance_events(
        db,
        start_date=start_date,
        end_date=end_date,
        username=username
    )
    
    # Process data for report
    employee_data = {}
    for employee in employees:
        # If username filter is applied, skip other employees
        if username and employee.username != username:
            continue
            
        employee_data[employee.id] = {
            "id": employee.id,
            "username": employee.username,
            "rfid": employee.rfid,
            "events": [],
            "total_days": 0,
            "total_hours": 0
        }
    
    # Calculate employee statistics
    calculate_employee_statistics(events, employee_data)
    
    # Prepare CSV data
    csv_data = [
        # Main report headers
        ['Username', 'RFID', 'Days Present', 'Total Hours']
    ]
    
    # Write summary data for each employee
    for emp_id, data in employee_data.items():
        csv_data.append([
            data["username"],
            data["rfid"],
            data["total_days"],
            f"{data['total_hours']:.2f}"
        ])
    
    # Add separator and headers for details
    csv_data.append([])  # Empty row as separator
    csv_data.append(['Detailed Entries'])
    csv_data.append(['Employee', 'Event Type', 'Timestamp'])
    
    # Sort all events by timestamp
    all_events_sorted = sorted(events, key=lambda e: e.timestamp)
    
    # Add detail rows
    for event in all_events_sorted:
        if event.user_id in employee_data:
            csv_data.append([
                employee_data[event.user_id]["username"],
                event.event_type,
                event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ])
    
    # Generate filename with current timestamp and date range
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add employee name to filename if filtered
    if username:
        filename = f"attendance_report_{username}_{start_str}_to_{end_str}_{timestamp}.csv"
    else:
        filename = f"attendance_report_{start_str}_to_{end_str}_{timestamp}.csv"
    
    # Return CSV response
    return create_csv_response(csv_data, filename)

# Helper function for report generation
def calculate_employee_statistics(events: List[models.AttendanceEvent], employee_data: Dict[int, Dict[str, Any]]):
    """Calculate statistics for each employee based on their attendance events"""
    # Group events by employee and date
    daily_events = {}
    for event in events:
        employee_id = event.user_id
        event_date = event.timestamp.date().isoformat()
        
        # Add event to employee data
        if employee_id in employee_data:
            employee_data[employee_id]["events"].append(event)
            
        # Group by date for daily calculations
        key = f"{employee_id}_{event_date}"
        if key not in daily_events:
            daily_events[key] = []
        daily_events[key].append(event)
    
    # Calculate daily totals
    for key, day_events in daily_events.items():
        # Sort events by timestamp
        day_events.sort(key=lambda e: e.timestamp)
        
        # Process checkins and checkouts
        checkins = [e for e in day_events if e.event_type == "checkin"]
        checkouts = [e for e in day_events if e.event_type == "checkout"]
        
        employee_id = day_events[0].user_id
        if employee_id not in employee_data:
            continue
            
        # If we have at least one checkin and checkout, calculate hours
        if checkins and checkouts:
            employee_data[employee_id]["total_days"] += 1
            
            # Match each checkin with the next checkout
            total_seconds = 0
            for i, checkin in enumerate(checkins):
                # Find the next checkout after this checkin
                matching_checkout = None
                for checkout in checkouts:
                    if checkout.timestamp > checkin.timestamp:
                        matching_checkout = checkout
                        break
                
                if matching_checkout:
                    # Calculate duration in seconds
                    duration = (matching_checkout.timestamp - checkin.timestamp).total_seconds()
                    total_seconds += duration
            
            # Add to employee total hours (convert seconds to hours)
            if total_seconds > 0:
                employee_data[employee_id]["total_hours"] += total_seconds / 3600

