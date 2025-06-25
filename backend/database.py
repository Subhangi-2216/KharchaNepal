from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import create_engine
from config import settings

# Convert async database URL to sync for compatibility with sync operations
def get_sync_database_url(async_url: str) -> str:
    """Convert async database URL to sync version."""
    if "+asyncpg" in async_url:
        return async_url.replace("+asyncpg", "+psycopg2")
    elif "+aiosqlite" in async_url:
        return async_url.replace("+aiosqlite", "")
    else:
        # If no async driver specified, assume it's already sync-compatible
        return async_url

# Use async engine for FastAPI compatibility
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Log SQL queries, useful for debugging
)

# Create sync engine for operations that require sync sessions
sync_engine = create_engine(
    get_sync_database_url(settings.DATABASE_URL),
    echo=True, # Log SQL queries, useful for debugging
)

# Use AsyncSession for asynchronous sessions
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Use Session for synchronous sessions (for gmail_service and other sync operations)
SessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency to get DB session in FastAPI routes
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session