import asyncio
from typing import Generator, Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import the main application and base model for table creation
from main import app # Your main FastAPI app
from database import Base # Your SQLAlchemy Base
from database import get_db # Original get_db dependency

# Use an in-memory SQLite database for testing
# Note: Async SQLite requires aiosqlite (pip install aiosqlite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db" 

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create test database tables before tests run and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Optional: Drop tables after tests if needed, but often left for inspection
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture()
async def db_session() -> AsyncSession:
    """Provide a test database session."""
    async with TestingSessionLocal() as session:
        yield session
        # Clean up if needed, though tests often rely on fresh DB each session
        # await session.rollback()

@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncClient:
    """Provide a test client that uses the test database session."""
    
    # Override the get_db dependency for the test client
    def override_get_db():
        try:
            yield db_session
        finally:
            # Ensure session is closed if needed, though handled by context manager
            pass 
            # await db_session.close() # Not needed with async context manager

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

    # Clean up overrides after tests
    app.dependency_overrides.clear() 