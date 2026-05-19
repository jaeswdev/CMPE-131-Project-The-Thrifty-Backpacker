"""
User ORM model.

Schema notes:
- Field names use PascalCase_With_Underscores to match the Phase 3 seed SQL
  (see Phase 3 handout, Part 2 step 5).
- `Tenant_ID` foreign key is added now as an Integer column. Anahi will add the
  FK constraint when her Tenant model lands (Task #10).
- `Password_Hash` stores the bcrypt hash, never the raw password.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "Users"

    User_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)
    First_Name = Column(String(50), nullable=False)
    Last_Name = Column(String(50), nullable=False)
    Email = Column(String(120), nullable=False, unique=True, index=True)
    Phone_Number = Column(String(20), nullable=True)
    Password_Hash = Column(String(255), nullable=False)

    # Multi-tenancy: which agency this user belongs to.
    # Anahi adds the ForeignKey("Tenants.Tenant_ID") in Task #13 once Tenants exists.
    Tenant_ID = Column(Integer, nullable=False, index=True)

    Created_At = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<User(User_ID={self.User_ID}, Email={self.Email}, Tenant_ID={self.Tenant_ID})>"