"""
Tenant resolution middleware.

Identifies the current tenant for each request and attaches it to
`request.state.tenant` so downstream endpoints can scope their queries.

Resolution order:
  1. `X-Tenant-Subdomain` header (developer override — used in Swagger UI)
  2. Subdomain extracted from the `Host` header (production path)
  3. If neither resolves, `request.state.tenant` is left as None
     (non-tenant endpoints like /health and /docs still work).

The middleware NEVER raises on missing tenants — that's the job of
`get_current_tenant` in app/api/deps.py, which is used only by
endpoints that actually require tenant scoping.
"""

from typing import Optional

from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import SessionLocal
from app.models.tenant import Tenant


# Domain suffixes the middleware recognizes. Anything ending in these gets
# its leading label treated as a subdomain. Hosts not matching are ignored.
TENANT_HOST_SUFFIXES = (".local", ".localhost")


def _extract_subdomain_from_host(host_header: Optional[str]) -> Optional[str]:
    """Pull the tenant subdomain out of a Host header like 'agenta.local:5173'."""
    if not host_header:
        return None

    # Strip port (e.g. ":5173") before parsing.
    host = host_header.split(":")[0].lower()

    # Only treat *.local / *.localhost as tenant hosts.
    if not host.endswith(TENANT_HOST_SUFFIXES):
        return None

    # First label is the subdomain. "agenta.local" -> "agenta"
    label = host.split(".")[0]
    return label or None


def _lookup_tenant(db: Session, subdomain: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.Subdomain == subdomain).first()


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolve the current Tenant and attach it to request.state.tenant."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Default: no tenant attached.
        request.state.tenant = None

        # Resolution order: header override first, then Host parsing.
        subdomain = (
            request.headers.get("x-tenant-subdomain")
            or _extract_subdomain_from_host(request.headers.get("host"))
        )

        if subdomain:
            db: Session = SessionLocal()
            try:
                tenant = _lookup_tenant(db, subdomain.lower())
                if tenant is not None:
                    # Detach from the session so the endpoint can read attrs
                    # after we close `db` below. We only need primitive fields.
                    db.expunge(tenant)
                    request.state.tenant = tenant
            finally:
                db.close()

        return await call_next(request)