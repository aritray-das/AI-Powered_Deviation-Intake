"""
database.py
-----------
Creates the SQLAlchemy engine and session factory.
All database interactions go through the get_db() dependency injected by FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# connect_args is not needed for MySQL (it's only required for SQLite)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # test connections before use to handle dropped connections
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class that all ORM models inherit from."""
    pass


def get_db():
    """
    FastAPI dependency that provides a database session per request,
    and guarantees the session is closed when the request is done.
    Usage in a route: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
