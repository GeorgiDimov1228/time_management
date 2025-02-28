from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app import schemas, crud, database, models, security
from typing import List
from app.database import get_db

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(security.get_current_admin_user)]
)


# @router.get("", response_model=List[schemas.EmployeeResponse])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.Employee = Depends(security.get_current_admin_user)):
#     users = crud.get_employees(db, skip=skip, limit=limit)
#     return users


# Changed from @router.get("/") to @router.get("")
@router.get("", response_model=List[schemas.EmployeeResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_employees(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.EmployeeResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_employee(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Changed from @router.post("/") to @router.post("")
@router.post("", response_model=schemas.EmployeeResponse)
def create_user(user: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_user = crud.create_employee(db, user)
    return db_user

@router.put("/{user_id}", response_model=schemas.EmployeeResponse)
def update_user(user_id: int, user: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    updated_user = crud.update_employee(db, user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    result = crud.delete_employee(db, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted successfully"}
