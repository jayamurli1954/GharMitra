"""
Pytest configuration and shared fixtures for GharMitra backend tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.config import settings


# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    session = async_session()
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest.fixture
async def client(test_db_session):
    """Create FastAPI test client with test database."""

    # Override the get_db dependency
    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
        "apartment_number": "A-101",
        "phone_number": "+91-9876543210",
        "role": "resident"
    }


@pytest.fixture
def sample_flat_data():
    """Sample flat data for testing."""
    return {
        "flat_number": "A-101",
        "area_sqft": 1200.0,
        "bedrooms": 3,
        "owner_name": "John Doe",
        "owner_phone": "+91-9876543210",
        "owner_email": "john@example.com",
        "occupants": 4,
        "occupancy_status": "owner_occupied"
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        "type": "expense",
        "category": "Maintenance",
        "account_code": "5001",
        "amount": 5000.00,
        "description": "Monthly maintenance charges",
        "date": "2024-01-15"
    }