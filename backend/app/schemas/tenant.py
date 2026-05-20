"""
Pydantic schemas for tenant-related endpoints.
"""

from pydantic import BaseModel


# Default fallback theme returned when a tenant has no logo/color configured
# (satisfies AC 4.3 — system must not crash or show broken images).
DEFAULT_LOGO_URL = "https://placehold.co/200x60/64748B/FFFFFF?text=Travel"
DEFAULT_BRAND_COLOR = "#64748B"  # neutral slate gray


class TenantInfoResponse(BaseModel):
    """Branding info returned to the UI for header rendering (US-4 AC 4.1, AC 4.3)."""
    Tenant_ID: int
    Name: str
    Subdomain: str
    Logo_URL: str
    Brand_Color: str
    Has_Custom_Theme: bool

    model_config = {"from_attributes": True}