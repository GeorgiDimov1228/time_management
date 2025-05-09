from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, time, timezone
from typing import Optional
import urllib.parse

from app import models, schemas, crud, security
from app.database import get_async_db

# Create templates instance
templates = Jinja2Templates(directory="app/templates")

# Create router with prefix
router = APIRouter(prefix="/admin", tags=["admin"])

# --- Authentication Routes ---

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_async_db)
):
    # Verify credentials
    user = await crud.get_employee_by_username(db, username=username)
    
    if not user or not security.pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse(
            "admin/login.html", 
            {"request": request, "error": "Invalid username or password"}
        )
    
    if not user.is_admin:
        return templates.TemplateResponse(
            "admin/login.html", 
            {"request": request, "error": "You do not have admin privileges"}
        )
    
    # Create JWT token
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    # Set token in cookies for future requests
    response = RedirectResponse(url="/admin/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="admin_token", value=access_token, httponly=True, max_age=1800)
    
    return response

@router.get("/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="admin_token")
    return response

# --- Middleware Dependency for Admin Auth ---

async def get_current_admin(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    # Check for the admin token cookie
    token = request.cookies.get("admin_token")
    if not token:
        print("Admin auth failed: No token found in cookies")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authenticated",
            headers={"Location": "/admin/login"}
        )
    
    try:
        # Verify token and get user ID
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        user_id = security.verify_token(token, credentials_exception)
        
        # Get user from DB and verify admin status
        user = await crud.get_employee(db, user_id=user_id)
        if not user:
            print(f"Admin auth failed: User {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                detail="User not found",
                headers={"Location": "/admin/login"}
            )
        
        if not user.is_admin:
            print(f"Admin auth failed: User {user.username} is not admin")
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                detail="Not admin",
                headers={"Location": "/admin/login"}
            )
        
        # Return the user object for route handlers
        return user
    except Exception as e:
        print(f"Admin auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, 
            detail="Invalid authentication",
            headers={"Location": "/admin/login"}
        )

# --- Helper Functions ---

def get_date_ranges():
    """Generate commonly used date ranges for templates"""
    now = datetime.now(timezone.utc)
    
    # Today
    today_start = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)
    
    # This week (Monday to Sunday)
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = (week_start + timedelta(days=6, hours=23, minutes=59, seconds=59))
    
    # This month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Get last day of month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)
    month_end = (next_month - timedelta(days=1)).replace(hour=23, minute=59, second=59)
    
    # Last month
    if now.month == 1:
        last_month_start = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        last_month_start = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    last_month_end = (month_start - timedelta(seconds=1))
    
    return {
        "today_start": today_start.isoformat(),
        "today_end": today_end.isoformat(),
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "month_start": month_start.isoformat(),
        "month_end": month_end.isoformat(),
        "last_month_start": last_month_start.isoformat(),
        "last_month_end": last_month_end.isoformat(),
    }

# --- Admin Routes ---

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get dashboard data
    # 1. Employee count
    result = await db.execute(select(models.Employee))
    all_employees = result.scalars().all()
    employee_count = len(all_employees)
    
    # 2. Today's check-ins and check-outs
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)
    
    checkin_events = await crud.get_filtered_attendance_events(
        db, 
        start_date=today_start, 
        end_date=today_end, 
        event_type="checkin"
    )
    checkin_count = len(checkin_events)
    
    checkout_events = await crud.get_filtered_attendance_events(
        db, 
        start_date=today_start, 
        end_date=today_end, 
        event_type="checkout"
    )
    checkout_count = len(checkout_events)
    
    # 3. Recent activity (all events from today)
    recent_events = await crud.get_filtered_attendance_events(
        db, 
        start_date=today_start, 
        end_date=today_end
    )
    # Sort by timestamp, most recent first
    recent_events.sort(key=lambda x: x.timestamp, reverse=True)
    # Limit to 10 most recent
    recent_events = recent_events[:10]
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "active_page": "dashboard",
            "employee_count": employee_count,
            "checkin_count": checkin_count,
            "checkout_count": checkout_count,
            "recent_events": recent_events
        }
    )

@router.get("/filtered-attendance", response_class=HTMLResponse)
async def filtered_attendance_view(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    username: Optional[str] = None,
    user_id: Optional[str] = None,
    manual: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    events = []
    filtered = False
    query_string = ""
    
    # Process input parameters
    parsed_start_date = None
    parsed_end_date = None
    parsed_user_id = None
    parsed_manual = None
    
    # Parse dates if provided
    if start_date and start_date.strip():
        try:
            parsed_start_date = datetime.fromisoformat(start_date)
        except ValueError:
            # Handle invalid date format
            pass
    
    if end_date and end_date.strip():
        try:
            parsed_end_date = datetime.fromisoformat(end_date)
        except ValueError:
            # Handle invalid date format
            pass
    
    # Parse user_id if provided
    if user_id and user_id.strip():
        try:
            parsed_user_id = int(user_id)
        except ValueError:
            # Handle invalid user_id
            pass
    
    # Parse manual if provided
    if manual and manual.strip():
        parsed_manual = manual.lower() == "true"
    
    # If any filter is set, query the data
    if any([parsed_start_date, parsed_end_date, event_type, username, parsed_user_id, parsed_manual is not None]):
        filtered = True
        events = await crud.get_filtered_attendance_events(
            db,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            event_type=event_type if event_type else None,
            username=username if username else None,
            user_id=parsed_user_id,
            manual=parsed_manual
        )
        
        # Build query string for export link
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if event_type:
            params["event_type"] = event_type
        if username:
            params["username"] = username
        if user_id:
            params["user_id"] = user_id
        if manual:
            params["manual"] = manual
        
        query_string = urllib.parse.urlencode(params)
    
    return templates.TemplateResponse(
        "admin/filtered_attendance.html",
        {
            "request": request,
            "active_page": "filtered-attendance",
            "events": events,
            "filtered": filtered,
            "query_string": query_string
        }
    )

@router.get("/export-csv", response_class=HTMLResponse)
async def export_csv_view(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get date ranges for quick export links
    date_ranges = get_date_ranges()
    
    return templates.TemplateResponse(
        "admin/export_csv.html",
        {
            "request": request,
            "active_page": "export-csv",
            **date_ranges
        }
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports_view(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get date ranges for quick report links
    date_ranges = get_date_ranges()
    
    return templates.TemplateResponse(
        "admin/reports.html",
        {
            "request": request,
            "active_page": "reports",
            **date_ranges
        }
    )

@router.get("/employees", response_class=HTMLResponse)
async def employees_view(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get all employees from the database
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/employees.html",
        {
            "request": request,
            "active_page": "employees",
            "employees": employees
        }
    )

@router.get("/employees/add", response_class=HTMLResponse)
async def add_employee_form(
    request: Request,
    admin_user: models.Employee = Depends(get_current_admin)
):
    return templates.TemplateResponse(
        "admin/employee_form.html",
        {
            "request": request,
            "active_page": "employees",
            "employee": None  # No employee data for a new employee form
        }
    )

@router.post("/employees/add", response_class=HTMLResponse)
async def create_employee(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    rfid: str = Form(...),
    is_admin: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Validate form data
    if password != confirm_password:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": None,
                "error": "Passwords do not match"
            }
        )
    
    # Check if username already exists
    existing_user = await crud.get_employee_by_username(db, username=username)
    if existing_user:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": None,
                "error": f"Username '{username}' already exists"
            }
        )
    
    # Create new employee
    try:
        is_admin_bool = is_admin.lower() == "true"
        employee_data = schemas.EmployeeCreate(
            username=username,
            email=email,
            rfid=rfid,
            password=password,
            is_admin=is_admin_bool
        )
        await crud.create_employee(db=db, employee=employee_data)
        
        # Redirect to employees list with success message
        response = RedirectResponse(url="/admin/employees?success=Employee added successfully", status_code=status.HTTP_302_FOUND)
        return response
    except Exception as e:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": None,
                "error": f"Error creating employee: {str(e)}"
            }
        )

@router.get("/employees/{employee_id}", response_class=HTMLResponse)
async def edit_employee_form(
    request: Request,
    employee_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get employee from database
    employee = await crud.get_employee(db, user_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return templates.TemplateResponse(
        "admin/employee_form.html",
        {
            "request": request,
            "active_page": "employees",
            "employee": employee
        }
    )

@router.post("/employees/{employee_id}", response_class=HTMLResponse)
async def update_employee(
    request: Request,
    employee_id: int,
    username: str = Form(...),
    email: str = Form(...),
    rfid: str = Form(...),
    is_admin: str = Form(...),
    password: str = Form(None),
    confirm_password: str = Form(None),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get employee from database
    employee = await crud.get_employee(db, user_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Validate form data
    if password and password != confirm_password:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": employee,
                "error": "Passwords do not match"
            }
        )
    
    # Check if username already exists for another employee
    existing_user = await crud.get_employee_by_username(db, username=username)
    if existing_user and existing_user.id != employee_id:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": employee,
                "error": f"Username '{username}' already exists for another employee"
            }
        )
    
    # Update employee
    try:
        is_admin_bool = is_admin.lower() == "true"
        employee_data = schemas.EmployeeUpdate(
            username=username,
            email=email,
            rfid=rfid,
            is_admin=is_admin_bool,
            password=password if password else None
        )
        await crud.update_employee(db=db, employee_id=employee_id, employee=employee_data)
        
        # Refresh employee data
        employee = await crud.get_employee(db, user_id=employee_id)
        
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": employee,
                "success": "Employee updated successfully"
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "admin/employee_form.html",
            {
                "request": request,
                "active_page": "employees",
                "employee": employee,
                "error": f"Error updating employee: {str(e)}"
            }
        )

@router.post("/employees/{employee_id}/delete")
async def delete_employee(
    request: Request,
    employee_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get employee from database
    employee = await crud.get_employee(db, user_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Prevent deleting yourself
    if employee_id == admin_user.id:
        return RedirectResponse(
            url=f"/admin/employees?error=Cannot delete your own account",
            status_code=status.HTTP_302_FOUND
        )
    
    # Delete employee
    try:
        await crud.delete_employee(db=db, user_id=employee_id)
        return RedirectResponse(
            url="/admin/employees?success=Employee deleted successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/employees?error=Error deleting employee: {str(e)}",
            status_code=status.HTTP_302_FOUND
        )

@router.get("/attendance", response_class=HTMLResponse)
async def attendance_view(
    request: Request,
    date_range: Optional[str] = None,
    event_type: Optional[str] = None,
    manual: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Default to no filter
    start_date = None
    end_date = None
    manual_bool = None
    filtered = False
    
    if date_range or event_type or manual:
        filtered = True
    
    # Handle date range filter
    now = datetime.now(timezone.utc)
    if date_range == "today":
        start_date = datetime.combine(now.date(), time.min).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(now.date(), time.max).replace(tzinfo=timezone.utc)
    elif date_range == "yesterday":
        yesterday = now - timedelta(days=1)
        start_date = datetime.combine(yesterday.date(), time.min).replace(tzinfo=timezone.utc)
        end_date = datetime.combine(yesterday.date(), time.max).replace(tzinfo=timezone.utc)
    elif date_range == "week":
        # Start of week (Monday)
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        # End of week (Sunday)
        week_end = (week_start + timedelta(days=6, hours=23, minutes=59, seconds=59))
        start_date = week_start
        end_date = week_end
    elif date_range == "month":
        # Start of month (1st day)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # End of month (last day)
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        month_end = (next_month - timedelta(days=1)).replace(hour=23, minute=59, second=59)
        start_date = month_start
        end_date = month_end
    elif date_range == "last-month":
        # Start of last month
        if now.month == 1:
            last_month_start = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            last_month_start = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # End of last month
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_end = (month_start - timedelta(seconds=1))
        
        start_date = last_month_start
        end_date = last_month_end
    
    # Handle manual filter
    if manual is not None:
        if manual.lower() == "true":
            manual_bool = True
        elif manual.lower() == "false":
            manual_bool = False
    
    # Get filtered events
    events = await crud.get_filtered_attendance_events(
        db,
        start_date=start_date,
        end_date=end_date,
        event_type=event_type,
        manual=manual_bool
    )
    
    # Sort by timestamp, most recent first
    events.sort(key=lambda x: x.timestamp, reverse=True)
    
    return templates.TemplateResponse(
        "admin/attendance.html",
        {
            "request": request,
            "active_page": "attendance",
            "events": events,
            "filtered": filtered,
            "date_range": date_range,
            "event_type": event_type,
            "manual": manual
        }
    )

# --- Manual Check In/Out Routes ---

@router.get("/manual-check", response_class=HTMLResponse)
async def manual_check_form(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get all employees for the dropdown
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/manual_check.html",
        {
            "request": request,
            "active_page": "manual-check",
            "employees": employees,
            "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
        }
    )

@router.post("/manual-check", response_class=HTMLResponse)
async def manual_check_submit(
    request: Request,
    user_id: int = Form(...),
    event_type: str = Form(...),
    timestamp: datetime = Form(...),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Validate event type
    if event_type not in ["checkin", "checkout"]:
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    # Get employee from database
    employee = await crud.get_employee(db, user_id=user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create attendance event
    try:
        event = models.AttendanceEvent(
            user_id=user_id,
            event_type=event_type,
            timestamp=timestamp,
            manual=True,
            notes=notes if notes else None
        )
        
        created_event = await crud.create_attendance_event(db, event_data=event)
        
        # Get all employees for the dropdown (for redisplay)
        result = await db.execute(select(models.Employee))
        employees = result.scalars().all()
        
        return templates.TemplateResponse(
            "admin/manual_check.html",
            {
                "request": request,
                "active_page": "manual-check",
                "employees": employees,
                "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M"),
                "success": f"Successfully recorded {event_type} for {employee.username} at {timestamp}"
            }
        )
    except Exception as e:
        # Get all employees for the dropdown (for redisplay)
        result = await db.execute(select(models.Employee))
        employees = result.scalars().all()
        
        return templates.TemplateResponse(
            "admin/manual_check.html",
            {
                "request": request,
                "active_page": "manual-check",
                "employees": employees,
                "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M"),
                "error": f"Error creating attendance event: {str(e)}"
            }
        )

# --- Attendance Edit/Delete Routes ---

@router.get("/attendance/{event_id}/edit", response_class=HTMLResponse)
async def edit_attendance_form(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get attendance event
    event = await crud.get_attendance_event(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Get all employees for the dropdown
    result = await db.execute(select(models.Employee))
    employees = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/edit_attendance.html",
        {
            "request": request,
            "active_page": "attendance",
            "event": event,
            "employees": employees
        }
    )

@router.post("/attendance/{event_id}/edit", response_class=HTMLResponse)
async def update_attendance(
    request: Request,
    event_id: int,
    user_id: int = Form(...),
    event_type: str = Form(...),
    timestamp: datetime = Form(...),
    manual: str = Form(...),
    notes: str = Form(None),
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get attendance event
    event = await crud.get_attendance_event(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Validate event type
    if event_type not in ["checkin", "checkout"]:
        # Get all employees for the dropdown for re-rendering the form
        result = await db.execute(select(models.Employee))
        employees = result.scalars().all()
        
        return templates.TemplateResponse(
            "admin/edit_attendance.html",
            {
                "request": request,
                "active_page": "attendance",
                "event": event,
                "employees": employees,
                "error": "Invalid event type"
            }
        )
    
    # Convert manual to boolean
    manual_bool = manual.lower() == "true"
    
    # Update event
    event_data = {
        "user_id": user_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "manual": manual_bool,
        "notes": notes if notes else None
    }
    
    try:
        updated_event = await crud.update_attendance_event(db, event_id, event_data)
        
        # Redirect to attendance list with success message
        return RedirectResponse(
            url="/admin/attendance?success=Attendance record updated successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        # Get all employees for the dropdown for re-rendering the form
        result = await db.execute(select(models.Employee))
        employees = result.scalars().all()
        
        return templates.TemplateResponse(
            "admin/edit_attendance.html",
            {
                "request": request,
                "active_page": "attendance",
                "event": event,
                "employees": employees,
                "error": f"Error updating attendance record: {str(e)}"
            }
        )

@router.post("/attendance/{event_id}/delete")
async def delete_attendance(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin_user: models.Employee = Depends(get_current_admin)
):
    # Get attendance event
    event = await crud.get_attendance_event(db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Delete event
    try:
        await crud.delete_attendance_event(db, event_id)
        return RedirectResponse(
            url="/admin/attendance?success=Attendance record deleted successfully",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/attendance?error=Error deleting attendance record: {str(e)}",
            status_code=status.HTTP_302_FOUND
        ) 