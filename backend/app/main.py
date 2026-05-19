from contextlib import asynccontextmanager
from fastapi import FastAPI, Response

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them on Base.metadata.
# Add Anahi's models here as they land: from app.models import tenant, booking
from app.models import user # noqa: F401

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)
    yield
    # (No teardown logic needed for SQLite)

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)


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