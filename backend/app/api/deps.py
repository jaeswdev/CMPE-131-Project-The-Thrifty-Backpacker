"""
Shared FastAPI dependencies for endpoints.

Endpoints declare `current_user: User = Depends(get_current_user)` to require
an authenticated request. If the JWT is missing/invalid/expired, the request
is rejected with 401 before the endpoint runs.
"""

from app.models.tenant import Tenant
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# tokenUrl is the path clients hit to GET a token. Swagger UI uses this to
# show an "Authorize" button. We'll create /api/v1/users/login in Task #8.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the User from the Authorization: Bearer <jwt> header.

    Raises 401 if the token is missing, malformed, expired, or refers to a
    nonexistent user. Returns the SQLAlchemy User instance otherwise.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_error
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_error

    user = db.query(User).filter(User.User_ID == user_id).first()
    if user is None:
        raise credentials_error

    return user

def get_current_tenant(request: Request) -> Tenant:
    """
    Require that the tenant middleware resolved a Tenant for this request.

    Endpoints declare `current_tenant: Tenant = Depends(get_current_tenant)`
    to require tenant scoping. Raises 400 if no tenant was resolved
    (e.g. the request hit 127.0.0.1 with no X-Tenant-Subdomain header).
    """
    tenant = getattr(request.state, "tenant", None)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tenant could not be resolved for this request. "
                "Set the X-Tenant-Subdomain header (e.g. 'agenta') or "
                "access via a tenant subdomain like agenta.local."
            ),
        )
    return tenant