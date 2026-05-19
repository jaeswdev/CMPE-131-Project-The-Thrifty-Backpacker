"""
Database engine and session factory.
Provides a FastAPI dependency `get_db()` that endpoints inject for DB access.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# SQLite-specific connection arg required for multi-threaded FastAPI
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # set True to see all SQL statements in console (useful for debugging)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    FastAPI dependency that yields a DB session per request.
    Closes automatically when the request finishes (even if exception raised).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()