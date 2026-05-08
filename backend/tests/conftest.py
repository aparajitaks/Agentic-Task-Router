"""
tests/conftest.py
─────────────────────────────────────────────────────────────────────────────
WHY THIS FILE EXISTS
    Pytest fixtures are the building blocks of a good test suite.  conftest.py
    is automatically loaded by pytest and its fixtures are available to ALL
    test files in the same directory and below.

WHAT IT DOES
    - Creates a separate in-memory SQLite database for tests (no real Postgres needed)
    - Provides an `async_client` fixture — an httpx.AsyncClient that talks to the
      test FastAPI app through real HTTP requests
    - Ensures each test runs in its own isolated database transaction

HOW IT CONNECTS
    tests/test_tasks.py  → uses `async_client` and `db_session` fixtures
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app

# ─────────────────────────────────────────────────────────────────────────────
# Test Database Setup
# ─────────────────────────────────────────────────────────────────────────────
# We use SQLite in-memory for speed.  The `check_same_thread=False` and
# `StaticPool` are required for SQLite to work with async SQLAlchemy.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    Create all tables before each test, drop them after.

    `autouse=True` means this runs automatically for every test function.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean database session for each test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an async HTTP test client wired to the FastAPI app.

    Overrides the `get_db` dependency so routes use the test database session
    instead of the real PostgreSQL database.
    """
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
