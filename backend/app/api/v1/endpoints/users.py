"""
User authentication endpoints.

Endpoints in this module follow the Phase 3 contract (Phase 3 PDF, page 1):
- GET /api/v1/users/login  → authenticate, return JWT + User_ID
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import SignupRequest, TokenResponse

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

    responses={
        200: {"description": "Authentication successful."},
        401: {"description": "Invalid email or password."},
    },
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

@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user and return a JWT",
    description=(
        "Creates a new User with a bcrypt-hashed password. Returns a JWT access "
        "token + User_ID so the client is logged in immediately. Returns 409 if "
        "the email is already taken within the same tenant."
    ),
    responses={
        201: {"description": "User created successfully."},
        409: {"description": "Email already registered."},
        422: {"description": "Validation error (missing fields, bad email, weak password, etc.)."},
    },
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    new_user = User(
        First_Name=payload.First_Name,
        Last_Name=payload.Last_Name,
        Email=payload.Email,
        Phone_Number=payload.Phone_Number,
        Password_Hash=hash_password(payload.Password),
        Tenant_ID=payload.Tenant_ID,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    access_token = create_access_token(subject=new_user.User_ID)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        User_ID=new_user.User_ID,
    )