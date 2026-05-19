"""
Pydantic schemas for authentication endpoints.

- Schemas define the SHAPE of data crossing the API boundary.
- They are separate from ORM models — ORM models are storage; schemas are wire format.
"""

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request body for POST /users/signup."""
    First_Name: str = Field(min_length=1, max_length=50)
    Last_Name: str = Field(min_length=1, max_length=50)
    Email: EmailStr
    Phone_Number: str | None = Field(default=None, max_length=20)
    Password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for POST /users/login (we also support GET via query params later)."""
    Email: EmailStr
    Password: str


class TokenResponse(BaseModel):
    """Response from a successful login or signup."""
    access_token: str
    token_type: str = "bearer"
    User_ID: int


class UserResponse(BaseModel):
    """Safe user representation — never includes Password_Hash."""
    User_ID: int
    First_Name: str
    Last_Name: str
    Email: EmailStr
    Phone_Number: str | None = None
    Tenant_ID: int

    model_config = {"from_attributes": True}  # lets Pydantic read from ORM objects