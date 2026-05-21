from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import bookings, search, tenants, trip, users
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them on Base.metadata.
from app.models import booking, booking_cache, tenant, user # noqa: F401

def _migrate_flight_cache_return_columns():
    """
    Idempotent SQLite migration: add the Return_* columns to FlightCache if
    they don't already exist. create_all() above only creates missing tables;
    it never alters existing ones, so a column added after the table was
    originally seeded won't appear without this.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if "FlightCache" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("FlightCache")}
    additions = [
        ("Return_Departure_Airport_Code", "VARCHAR(10)"),
        ("Return_Departure_Airport_Name", "VARCHAR(200)"),
        ("Return_Departure_City", "VARCHAR(100)"),
        ("Return_Departure_Datetime", "DATETIME"),
        ("Return_Arrival_Airport_Code", "VARCHAR(10)"),
        ("Return_Arrival_Airport_Name", "VARCHAR(200)"),
        ("Return_Arrival_City", "VARCHAR(100)"),
        ("Return_Arrival_Datetime", "DATETIME"),
        ("Return_Duration_Minutes", "INTEGER"),
        ("Return_Stops", "INTEGER"),
    ]
    with engine.begin() as conn:
        for name, sql_type in additions:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE FlightCache ADD COLUMN {name} {sql_type}"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)
    _migrate_flight_cache_return_columns()
    yield
    # (No teardown logic needed for SQLite)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# Middleware (registered in reverse order of execution - last added runs first)
from app.middleware.tenant import TenantMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

# Routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"])
app.include_router(trip.router, prefix="/api/v1/trip", tags=["trip"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

