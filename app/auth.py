# app/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session # <-- REMOVE
from datetime import timedelta
from app import crud, models, security # Import async crud
# from app.database import get_db # <-- REMOVE

# Define the router
router = APIRouter()

# --- Make route async, remove db dependency, await crud call ---
@router.post("/token")
async def login_for_access_token( # <-- async def
    form_data: OAuth2PasswordRequestForm = Depends(),
    # db: Session = Depends(get_db) # <-- REMOVE
):
    # Call the async version of the crud function, no db needed
    user = await crud.get_employee_by_username(form_data.username) # <-- await

    # Password verification and token creation are typically CPU-bound sync operations,
    # which are okay to call directly in an async function (FastAPI handles them).
    if not user or not security.pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        # Ensure user.id exists and is the correct type after Tortoise migration
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}