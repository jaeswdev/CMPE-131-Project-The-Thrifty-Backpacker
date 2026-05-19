"""
Password hashing and JWT token utilities.

- Passwords are hashed with bcrypt (work factor 12, industry standard for 2026).
- JWTs are HS256-signed with settings.JWT_SECRET.
- Token payload: {"sub": <user_id>, "exp": <unix timestamp>}.

Note: We use the `bcrypt` library directly rather than `passlib`. As of 2024+,
passlib is unmaintained and incompatible with bcrypt 4.x. Direct bcrypt is
simpler and avoids the compatibility issue.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings

# bcrypt enforces a 72-byte password limit. Truncate defensively
# so we never crash on long passwords.
_BCRYPT_MAX_BYTES = 72


# === Password hashing ===

def hash_password(plain_password: str) -> str:
    """Return a bcrypt hash of the password. Use this when creating a user."""
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a submitted password against the stored hash. Returns True if match."""
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# === JWT creation and verification ===

def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    """
    Build a signed JWT.
    `subject` is whatever identifies the user — usually User_ID.
    """
    expire_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),      # JWT spec requires "sub" to be a string
        "exp": expire_at,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT. Raises JWTError if the token is invalid or expired.
    Returns the decoded payload dict.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])