"""
Seed script — initializes the database with starter test data.

Run with: uv run python -m scripts.seed (from the `backend/` folder)

Idempotent: safe to run multiple times. Existing rows are NOT duplicated.
"""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User


def seed_tenants(db: Session) -> None:
    """
    Per Phase 1 TC-08, we need three tenants for branding tests.
    """
    tenants = [
        Tenant(
            Tenant_ID=1,
            Name="Travel Agency A",
            Subdomain="agenta",
            Logo_URL="https://placehold.co/200x60/1E40AF/FFFFFF?text=Agency+A",
            Brand_Color="#1E40AF",  # blue per TC-08
        ),
        Tenant(
            Tenant_ID=2,
            Name="Travel Agency B",
            Subdomain="agentb",
            Logo_URL="https://placehold.co/200x60/047857/FFFFFF?text=Agency+B",
            Brand_Color="#047857",  # green per TC-08
        ),
        Tenant(
            Tenant_ID=3,
            Name="Travel Agency C",
            Subdomain="agentc",
            Logo_URL=None,           # AC 4.3: no theme configured
            Brand_Color=None,
        ),
    ]

    for tenant in tenants:
        existing = db.query(Tenant).filter(Tenant.Tenant_ID == tenant.Tenant_ID).first()
        if existing is None:
            db.add(tenant)
            print(f"  + Created {tenant.Name} (Tenant_ID={tenant.Tenant_ID})")
        else:
            print(f"  = {existing.Name} already exists (Tenant_ID={existing.Tenant_ID})")
    db.commit()


def seed_users(db: Session) -> None:
    """
    Seed two test users:
    - John Doe → Tenant A (per Phase 3 handout page 2 spec)
    - Hyunjae Lee → Tenant A as well, for our own testing
    """
    users = [
        User(
            First_Name="John",
            Last_Name="Doe",
            Email="john.doe@example.com",
            Phone_Number="555-123-4567",
            Password_Hash=hash_password("CMPE-131@2026"),
            Tenant_ID=1,  # Travel Agency A
        ),
        User(
            First_Name="Hyunjae",
            Last_Name="Lee",
            Email="hyunjae.lee@example.com",
            Phone_Number="408-555-0123",
            Password_Hash=hash_password("test-password-123"),
            Tenant_ID=1,
        ),
    ]

    for user in users:
        existing = db.query(User).filter(User.Email == user.Email).first()
        if existing is None:
            db.add(user)
            print(f"  + Created {user.First_Name} {user.Last_Name} <{user.Email}> (Tenant_ID={user.Tenant_ID})")
        else:
            print(f"  = {existing.Email} already exists (User_ID={existing.User_ID})")
    db.commit()


def main() -> None:
    print("Seeding database...")
    db = SessionLocal()
    try:
        print("\n[1/2] Tenants:")
        seed_tenants(db)
        print("\n[2/2] Users:")
        seed_users(db)
        print("\nDone.")
    finally:
        db.close()


if __name__ == "__main__":
    main()