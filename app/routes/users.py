from fastapi import APIRouter, HTTPException, Depends, FastAPI, Request
from app.security import pwd_context # Import pwd_context
# from sqlalchemy.orm import Session # <-- REMOVE
from app import schemas, crud, models, security # Keep models import for type hinting maybe
from typing import List
# from app.database import get_db # <-- REMOVE

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # This dependency is now async, so routes using it must be async
    dependencies=[Depends(security.get_current_admin_user)]
)

# --- Make routes async, remove db dependency, await crud calls ---

@router.get("", response_model=List[schemas.EmployeeResponse])
async def read_users(skip: int = 0, limit: int = 100): # <-- async def, removed db
    # Call async crud function, remove db argument
    users = await crud.get_employees(skip=skip, limit=limit) # <-- await
    return users

@router.get("/{user_id}", response_model=schemas.EmployeeResponse)
async def read_user(user_id: int): # <-- async def, removed db
    user = await crud.get_employee(user_id=user_id) # <-- await, remove db argument
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=schemas.EmployeeResponse)
async def create_user(user: schemas.EmployeeCreate): # <-- async def, removed db
    # Ensure crud.create_employee handles potential IntegrityError (e.g., duplicate username)
    # and maybe raises an HTTPException(409, detail="Username/Email/RFID already exists")
    db_user = await crud.create_employee(employee=user) # <-- await, remove db argument
    if db_user is None:
         # Handle potential creation error if crud function returns None on IntegrityError
         raise HTTPException(status_code=409, detail="Username, Email, or RFID may already exist.")
    return db_user

@router.put("/{user_id}", response_model=schemas.EmployeeResponse)
async def update_user(user_id: int, user: schemas.EmployeeCreate): # <-- async def, removed db
    # Note: EmployeeCreate schema includes password - consider a separate EmployeeUpdate schema?
    updated_user = await crud.update_employee(user_id=user_id, employee=user) # <-- await, remove db argument
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.put("/{user_id}/password", response_model=schemas.EmployeeResponse)
async def update_user_password( # <-- async def
    user_id: int,
    password_data: schemas.PasswordUpdate,
    # db: Session = Depends(get_db) # <-- REMOVE
):
    # crud.update_password is now async
    result = await crud.update_password( # <-- await, remove db argument
        user_id=user_id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    elif result is False:
        # Consider checking the return type, crud.update_password might return the user obj on success
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Assuming crud.update_password returns the updated user object on success
    return result

@router.delete("/{user_id}")
async def delete_user(user_id: int): # <-- async def, removed db
    result = await crud.delete_employee(user_id=user_id) # <-- await, remove db argument
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}