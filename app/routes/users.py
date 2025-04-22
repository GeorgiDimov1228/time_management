# time_management/app/routes/users.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession # Use AsyncSession
# from sqlalchemy.orm import Session # Keep if update_password stays sync

from app import crud, schemas, models # Import models if needed for dependencies
from app.database import get_async_db # Use async dependency
# from app.database import get_db # Keep if update_password stays sync
from app.security import get_current_admin_user_async # Use async admin dependency

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # Use async dependency for admin check
    dependencies=[Depends(get_current_admin_user_async)]
)

@router.get("", response_model=List[schemas.EmployeeResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
):
    # Ensure this calls the async crud function
    users = await crud.get_employees(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.EmployeeResponse)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
     # Ensure this calls the async crud function
    user = await crud.get_employee(db, user_id=user_id) # Pass user_id directly
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=schemas.EmployeeResponse)
async def create_user(
    user: schemas.EmployeeCreate,
    db: AsyncSession = Depends(get_async_db),
):
    # Ensure this calls the async crud function
    db_user = await crud.get_employee_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await crud.create_employee(db=db, employee=user)


@router.put("/{user_id}", response_model=schemas.EmployeeResponse)
async def update_user(
    user_id: int,
    user_update: schemas.EmployeeCreate, # Rename variable for clarity
    db: AsyncSession = Depends(get_async_db),
):
    # Ensure this calls the async crud function
    updated_user = await crud.update_employee(db, user_id=user_id, employee_update=user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# OPTION 1: Keep password update sync (Requires sync crud.get_employee and sync crud.update_password)
# from app.database import get_db
# @router.put("/{user_id}/password", response_model=schemas.EmployeeResponse)
# def update_user_password_sync(
#     user_id: int,
#     pwd: schemas.PasswordUpdate,
#     db: Session = Depends(get_db), # Sync DB
# ):
#     # Call sync crud functions here...
#     db_emp = crud.get_employee(db, user_id) # Needs sync version
#     if not db_emp:
#          raise HTTPException(404, "User not found")
#     result = crud.update_password( # Needs sync version
#         db, user_id, pwd.current_password, pwd.new_password
#     )
#     # ... rest of sync logic

# OPTION 2: Make password update async (Recommended if possible)
@router.put("/{user_id}/password", response_model=schemas.EmployeeResponse)
async def update_user_password_async( # Make async
    user_id: int,
    pwd: schemas.PasswordUpdate,
    db: AsyncSession = Depends(get_async_db), # Async DB
):
    # Call async crud functions
    result = await crud.update_password( # Call async version
        db, user_id, pwd.current_password, pwd.new_password
    )
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Current password incorrect")
    # If result is the user object on success:
    return result # Assuming crud.update_password returns the updated user model


@router.delete("/{user_id}", response_model=schemas.EmployeeResponse) # Return deleted user? Or just status?
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    # Ensure this calls the async crud function
    deleted_user = await crud.delete_employee(db, user_id=user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    # Return the deleted user object (as per response_model)
    return deleted_user
    # Or return a success message:
    # return {"detail": "User deleted successfully"} # Change response_model if using this