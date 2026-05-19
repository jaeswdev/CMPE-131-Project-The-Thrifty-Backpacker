"""
User authentication endpoints.

Endpoints in this module follow the Phase 3 contract (Phase 3 PDF, page 1):
- GET /api/v1/users/login  → authenticate, return JWT + User_ID
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse

router = APIRouter()


@router.get(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate a user by email and password",
    description=(
        "Phase 3 contract endpoint. Validates credentials and returns a "
        "JWT access token plus the User_ID. Returns 401 if email is not found "
        "or password does not match."
    ),
)
def login(
    email: EmailStr = Query(..., description="Registered email address"),
    password: str = Query(..., min_length=1, description="Account password"),
    db: Session = Depends(get_db),
):
    """Authenticate the user and return a JWT."""
    # Generic error keeps us from leaking which check failed.
    auth_failed = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )

    user = db.query(User).filter(User.Email == email).first()
    if user is None:
        raise auth_failed

    if not verify_password(password, user.Password_Hash):
        raise auth_failed

    access_token = create_access_token(subject=user.User_ID)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        User_ID=user.User_ID,
    )