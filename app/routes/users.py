from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_async_db, get_db
from app.security import get_current_admin_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.get("", response_model=List[schemas.EmployeeResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db),
):
    users = await crud.get_employees(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.EmployeeResponse)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    user = await crud.get_employee(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.post("", response_model=schemas.EmployeeResponse)
async def create_user(
    user: schemas.EmployeeCreate,
    db: AsyncSession = Depends(get_async_db),
):
    return await crud.create_employee(db, user)

@router.put("/{user_id}", response_model=schemas.EmployeeResponse)
async def update_user(
    user_id: int,
    user: schemas.EmployeeCreate,
    db: AsyncSession = Depends(get_async_db),
):
    updated = await crud.update_employee(db, user_id, user)
    if not updated:
        raise HTTPException(404, "User not found")
    return updated

@router.put("/{user_id}/password", response_model=schemas.EmployeeResponse)
def update_user_password(
    user_id: int,
    pwd: schemas.PasswordUpdate,
    db: Session = Depends(get_db),          # keep sync here since update_password is sync
):
    # verify exist
    db_emp = crud.get_employee(db, user_id)
    if not db_emp:
        raise HTTPException(404, "User not found")

    result = crud.update_password(
        db, user_id, pwd.current_password, pwd.new_password
    )
    if result is False:
        raise HTTPException(400, "Current password is incorrect")
    return result

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    deleted = await crud.delete_employee(db, user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    return {"detail": "User deleted"}
