"""
Bookings endpoints.

Task #22: GET /api/v1/bookings/by-agent-user
Returns all bookings for the currently logged-in user, scoped to their tenant.
Implements US-4 AC 4.2 tenant isolation — a user from Tenant A cannot see
Tenant B's bookings.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant, get_current_user
from app.db.session import get_db
from app.models.booking import Booking
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.booking import BookingResponse

router = APIRouter()


@router.get(
    "/by-agent-user",
    response_model=list[BookingResponse],
    summary="Get all bookings for the current user",
    description=(
        "Returns every booking belonging to the authenticated user, scoped to "
        "their tenant. A user from Tenant A will never see Tenant B bookings "
        "(AC 4.2 tenant isolation)."
    ),
    responses={
        200: {"description": "List of bookings (may be empty)."},
        401: {"description": "Missing or invalid JWT."},
        400: {"description": "Tenant could not be resolved."},
    },
)
def get_bookings_by_agent_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> list[BookingResponse]:
    bookings = (
        db.query(Booking)
        .filter(
            Booking.User_ID == current_user.User_ID,
            Booking.Tenant_ID == current_tenant.Tenant_ID,
        )
        .order_by(Booking.Created_At.desc())
        .all()
    )
    return bookings
