"""
Tenant info endpoints.

Powers the branding UI per Phase 1 US-4:
- AC 4.1: Page header displays the logged-in tenant's logo, agency name, color.
- AC 4.3: System falls back to a neutral default if no theme is configured.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_tenant
from app.models.tenant import Tenant
from app.schemas.tenant import TenantInfoResponse, DEFAULT_BRAND_COLOR, DEFAULT_LOGO_URL

router = APIRouter()


@router.get(
    "/me",
    response_model=TenantInfoResponse,
    summary="Get the current tenant's branding info",
    description=(
        "Returns the agency name, logo URL, and primary brand color for the "
        "tenant resolved from the request. If the tenant has no logo or color "
        "configured, a neutral default theme is returned (US-4 AC 4.3)."
    ),
    responses={
        200: {"description": "Tenant info successfully returned."},
        400: {"description": "Tenant could not be resolved (missing subdomain)."},
    },
)
def get_current_tenant_info(
    tenant: Tenant = Depends(get_current_tenant),
):
    """Return the current tenant's branding info, with sensible defaults."""
    return TenantInfoResponse(
        Tenant_ID=tenant.Tenant_ID,
        Name=tenant.Name,
        Subdomain=tenant.Subdomain,
        Logo_URL=tenant.Logo_URL or DEFAULT_LOGO_URL,
        Brand_Color=tenant.Brand_Color or DEFAULT_BRAND_COLOR,
        Has_Custom_Theme=bool(tenant.Logo_URL and tenant.Brand_Color),
    )