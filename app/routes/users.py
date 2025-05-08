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
    db_user = await crud.get_employee_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await crud.create_employee(db=db, employee=user)


@router.put("/{user_id}", response_model=schemas.EmployeeResponse)
async def update_user(
    user_id: int,
    user_update: schemas.EmployeeCreate, 
    db: AsyncSession = Depends(get_async_db),
):
    updated_user = await crud.update_employee(db, user_id=user_id, employee_update=user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.put("/{user_id}/password", response_model=schemas.EmployeeResponse)
async def update_user_password_async( 
    user_id: int,
    pwd: schemas.PasswordUpdate,
    db: AsyncSession = Depends(get_async_db), # Async DB
):

    result = await crud.update_password( 
        db, user_id, pwd.current_password, pwd.new_password
    )
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Current password incorrect")
    # If result is the user object on success:
    return result 


@router.delete("/{user_id}", response_model=schemas.EmployeeResponse) 
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