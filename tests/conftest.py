import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base, get_db, get_async_db
from app.main import app
from app.models import Employee
from app.security import get_password_hash

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["TESTING"] = "true"

# Create engines
engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    connect_args={"check_same_thread": False}
)
AsyncTestingSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create tables
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    # Override dependencies
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async def override_get_async_db():
        async with AsyncTestingSessionLocal() as session:
            yield session
    
    app.dependency_overrides[get_async_db] = override_get_async_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    # Check if user already exists
    user = db_session.query(Employee).filter(Employee.username == "testuser").first()
    if user:
        return user
    
    # Create user
    user = Employee(
        username="testuser",
        email="test@example.com",
        rfid="1234567890",
        hashed_password=get_password_hash("testpassword"),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin(db_session):
    # Check if admin already exists
    admin = db_session.query(Employee).filter(Employee.username == "admin").first()
    if admin:
        return admin
    
    # Create admin
    admin = Employee(
        username="admin",
        email="admin@example.com",
        rfid="ADMIN123",
        hashed_password=get_password_hash("adminpassword"),
        is_admin=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin 