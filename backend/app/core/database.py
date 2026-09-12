"""
Database session and engine configuration using SQLAlchemy 2.0 async.

Usage:
    from app.core.database import get_db, engine

    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


# ── Engine ─────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # validates connections before checkout
)

# ── Session factory ─────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base for all ORM models ─────────────────────────────────────
class Base(DeclarativeBase):
    """All SQLAlchemy ORM models inherit from this base."""
    pass


# ── FastAPI dependency ───────────────────────────────────────────────────────
async def get_db() -> AsyncSession:  # type: ignore[return]
    """
    Dependency that provides a database session per request.
    The session is automatically closed when the request finishes.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
