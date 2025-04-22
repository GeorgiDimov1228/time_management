# time_management/app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker # Import sessionmaker for sync
from sqlalchemy import create_engine # Import create_engine for sync
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/time_management_db")
# Ensure the DATABASE_URL starts with postgresql+asyncpg://
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# --- Async Setup ---
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False) # Set echo=True for debug
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --- Sync Setup (Keep for SQLAdmin or other sync parts if needed) ---
sync_engine = create_engine(DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Base remains the same
Base = declarative_base()

# --- Async Dependency ---
async def get_async_db() -> AsyncSession:
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

# --- Sync Dependency ---
def get_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()