"""
Tenant ORM model.

Schema notes:
- Each tenant represents one travel agency on the SaaS platform.
- `Subdomain` is the lookup key for the tenant middleware — incoming requests
  hit `agenta.local`, `agentb.local`, etc., and middleware extracts the leading
  label to find the matching Tenant row.
- Logo_URL and Brand_Color are nullable to satisfy AC 4.3 (fallback to neutral
  default theme if a tenant has not configured them).
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "Tenants"

    Tenant_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    Name = Column(String(100), nullable=False)
    Subdomain = Column(String(50), nullable=False, unique=True, index=True)
    Logo_URL = Column(String(255), nullable=True)
    Brand_Color = Column(String(20), nullable=True)
    Created_At = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Tenant(Tenant_ID={self.Tenant_ID}, Name={self.Name}, Subdomain={self.Subdomain})>"