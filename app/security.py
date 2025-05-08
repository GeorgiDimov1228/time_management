# time_management/app/security.py
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session # Keep for sync version if needed
from sqlalchemy.ext.asyncio import AsyncSession 
from dotenv import load_dotenv

from app import crud, models
from app.database import get_db, get_async_db 

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token") 

def get_password_hash(password: str) -> str:
    """Generate a password hash from a plaintext password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Validate that user_id is an integer before returning
        try:
            return int(user_id)
        except (ValueError, TypeError):
             raise credentials_exception
    except JWTError:
        raise credentials_exception

# --- Async Dependency Functions ---

async def get_current_user_async(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_db)) -> models.Employee:
    """ Dependency to get the current user from token (async version). """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_token(token, credentials_exception)
    user = await crud.get_employee(db, user_id=user_id) 
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user_async(current_user: models.Employee = Depends(get_current_user_async)) -> models.Employee:
    """ Depends on get_current_user_async and checks admin status (async version). """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

async def get_current_authenticated_user_async(current_user: models.Employee = Depends(get_current_user_async)) -> models.Employee:
     """ Alias for get_current_user_async for clarity in routes needing any logged-in user (async version). """
     # This function just relies on get_current_user_async
     return current_user


# --- Sync Dependency Functions (Kept if needed for sync parts like /token or admin panel) ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Employee:
    """ Dependency to get the current user from token (sync version). """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_token(token, credentials_exception)
    user = crud.get_employee_sync(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
    """ Depends on get_current_user and checks admin status (sync version). """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def get_current_authenticated_user(current_user: models.Employee = Depends(get_current_user)) -> models.Employee:
    """ Alias for get_current_user for clarity (sync version). """
    return current_user