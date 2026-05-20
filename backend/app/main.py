from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response

from app.api.v1.endpoints import users
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import all models so SQLAlchemy registers them on Base.metadata.
from app.models import tenant, user # noqa: F401

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

@app.get("/__debug/tenant", tags=["debug"])
def debug_current_tenant(request: Request):
    """TEMPORARY: shows what the tenant middleware resolved for this request.
    Will be replaced by GET /api/v1/tenants/me in PR C."""
    tenant = getattr(request.state, "tenant", None)
    if tenant is None:
        return {"tenant": None, "resolved_from": "nothing"}
    return {
        "Tenant_ID": tenant.Tenant_ID,
        "Name": tenant.Name,
        "Subdomain": tenant.Subdomain,
        "Brand_Color": tenant.Brand_Color,
    }