"""
Database engine and session factory.
Provides a FastAPI dependency `get_db()` that endpoints inject for DB access.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# SQLite-specific connection arg required for multi-threaded FastAPI
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)


# SQLite ships with FOREIGN KEY constraints disabled by default. Turn them
# ON for every new connection so the FK from User.Tenant_ID -> Tenants is
# actually enforced (required for AC 4.2 data integrity).
if is_sqlite:
    @event.listens_for(Engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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