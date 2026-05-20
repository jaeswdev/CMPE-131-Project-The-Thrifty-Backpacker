from contextlib import asynccontextmanager
from fastapi import FastAPI, Response

from app.api.v1.endpoints import bookings, search, tenants, trip, users
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them on Base.metadata.
from app.models import booking, booking_cache, tenant, user # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)
    yield
    # (No teardown logic needed for SQLite)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

# Middleware (registered in reverse order of execution - last added runs first)
from app.middleware.tenant import TenantMiddleware
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

