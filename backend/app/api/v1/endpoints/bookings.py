"""
Booking endpoints (Phase 3 contract).

Currently implements POST /api/v1/bookings (Task #21).
Future tasks will add:
  - GET /api/v1/bookings/by-agent-user (Anahi, Task #22)
  - PUT /api/v1/bookings/{id} (Hyunjae, Task #23)
  - PATCH /api/v1/bookings/{id}/cancel (Hyunjae, Task #24)
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant, get_current_user
from app.db.session import get_db
from app.models.booking import Booking, BookingType
from app.models.booking_cache import AttractionCache, FlightCache, HotelCache
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.booking import (
    BookingResponse,
    CreateAttractionBookingRequest,
    CreateFlightBookingRequest,
    CreateHotelBookingRequest,
    FlightItemPayload,
    HotelItemPayload,
    AttractionItemPayload,
    UpdateBookingStatusRequest,
)

router = APIRouter()


# ============================================================================
# Cache helpers — each returns the new cache row's primary key
# ============================================================================

def _cache_flight(db: Session, payload: FlightItemPayload) -> FlightCache:
    cache_row = FlightCache(
        Offer_Token=payload.offer_token,
        Airline_Name=payload.airline_name,
        Airline_Code=payload.airline_code,
        Airline_Logo_URL=payload.airline_logo_url,
        Departure_Airport_Code=payload.departure_airport_code,
        Departure_Airport_Name=payload.departure_airport_name,
        Departure_City=payload.departure_city,
        Departure_Datetime=payload.departure_datetime,
        Arrival_Airport_Code=payload.arrival_airport_code,
        Arrival_Airport_Name=payload.arrival_airport_name,
        Arrival_City=payload.arrival_city,
        Arrival_Datetime=payload.arrival_datetime,
        Stops=payload.stops,
        Duration_Minutes=payload.duration_minutes,
        Price=payload.price,
        Currency=payload.currency,
        Trip_Type=payload.trip_type,
        Return_Departure_Airport_Code=payload.return_departure_airport_code,
        Return_Departure_Airport_Name=payload.return_departure_airport_name,
        Return_Departure_City=payload.return_departure_city,
        Return_Departure_Datetime=payload.return_departure_datetime,
        Return_Arrival_Airport_Code=payload.return_arrival_airport_code,
        Return_Arrival_Airport_Name=payload.return_arrival_airport_name,
        Return_Arrival_City=payload.return_arrival_city,
        Return_Arrival_Datetime=payload.return_arrival_datetime,
        Return_Duration_Minutes=payload.return_duration_minutes,
        Return_Stops=payload.return_stops,
    )
    db.add(cache_row)
    db.flush()  # Get the PK without committing yet
    return cache_row


def _cache_hotel(db: Session, payload: HotelItemPayload) -> HotelCache:
    if payload.checkout_date <= payload.checkin_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="checkout_date must be after checkin_date.",
        )

    cache_row = HotelCache(
        External_Hotel_ID=payload.external_hotel_id,
        Hotel_Name=payload.hotel_name,
        Accommodation_Type=payload.accommodation_type,
        Star_Class=payload.star_class,
        City=payload.city,
        Address=payload.address,
        Checkin_Date=payload.checkin_date,
        Checkout_Date=payload.checkout_date,
        Total_Price=payload.total_price,
        Price_Per_Night=payload.price_per_night,
        Currency=payload.currency,
        Photo_URL=payload.photo_url,
        Booking_URL=payload.booking_url,
    )
    db.add(cache_row)
    db.flush()
    return cache_row


def _cache_attraction(db: Session, payload: AttractionItemPayload) -> AttractionCache:
    if payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date.",
        )

    cache_row = AttractionCache(
        Offer_Token=payload.offer_token,
        Name=payload.name,
        Description=payload.description,
        City=payload.city,
        Price=payload.price,
        Currency=payload.currency,
        Rating=payload.rating,
        Has_Free_Cancellation=payload.has_free_cancellation,
        Start_Date=payload.start_date,
        End_Date=payload.end_date,
        Photo_URL=payload.photo_url,
        Booking_URL=payload.booking_url,
    )
    db.add(cache_row)
    db.flush()
    return cache_row


# ============================================================================
# Cache fetch helpers — used to attach the `item` dict to the response
# ============================================================================

def _fetch_cached_item(db: Session, booking: Booking) -> dict | None:
    """Look up the cached item for a booking and return it as a dict."""
    if booking.Booking_Type == BookingType.FLIGHT:
        row = db.query(FlightCache).filter(FlightCache.Flight_Cache_ID == booking.Cached_Item_ID).first()
    elif booking.Booking_Type == BookingType.HOTEL:
        row = db.query(HotelCache).filter(HotelCache.Hotel_Cache_ID == booking.Cached_Item_ID).first()
    elif booking.Booking_Type == BookingType.ATTRACTION:
        row = db.query(AttractionCache).filter(AttractionCache.Attraction_Cache_ID == booking.Cached_Item_ID).first()
    else:
        return None

    if row is None:
        return None

    # Convert SQLAlchemy row to a clean dict (skip private attrs)
    return {
        col.name: getattr(row, col.name)
        for col in row.__table__.columns
    }


def _booking_to_response(db: Session, booking: Booking) -> BookingResponse:
    """Build a BookingResponse including the cached item details."""
    return BookingResponse(
        Booking_ID=booking.Booking_ID,
        User_ID=booking.User_ID,
        Tenant_ID=booking.Tenant_ID,
        Booking_Type=booking.Booking_Type.value if hasattr(booking.Booking_Type, "value") else str(booking.Booking_Type),
        Cached_Item_ID=booking.Cached_Item_ID,
        Status=booking.Status.value if hasattr(booking.Status, "value") else str(booking.Status),
        Total_Price=booking.Total_Price,
        Currency=booking.Currency,
        Notes=booking.Notes,
        Created_At=booking.Created_At,
        Updated_At=booking.Updated_At,
        item=_fetch_cached_item(db, booking),
    )


# ============================================================================
# POST /bookings — three variants via separate endpoint paths
# ============================================================================

# We expose three separate endpoint paths even though Phase 3 contract says
# POST /bookings, because Pydantic's discriminated union handling becomes
# fragile across FastAPI versions. Three sub-paths with the same prefix
# achieves the same UX with simpler routing.

@router.post(
    "/flights",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a flight booking",
    description="Snapshots a flight offer into FlightCache and creates a tenant-scoped Booking row.",
)
def create_flight_booking(
    body: CreateFlightBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    cache_row = _cache_flight(db, body.flight)
    booking = Booking(
        User_ID=current_user.User_ID,
        Tenant_ID=current_tenant.Tenant_ID,
        Booking_Type=BookingType.FLIGHT,
        Cached_Item_ID=cache_row.Flight_Cache_ID,
        Total_Price=body.flight.price,
        Currency=body.flight.currency,
        Notes=body.notes,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_to_response(db, booking)


@router.post(
    "/hotels",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hotel booking",
    description="Snapshots a hotel into HotelCache and creates a tenant-scoped Booking row.",
)
def create_hotel_booking(
    body: CreateHotelBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    cache_row = _cache_hotel(db, body.hotel)
    booking = Booking(
        User_ID=current_user.User_ID,
        Tenant_ID=current_tenant.Tenant_ID,
        Booking_Type=BookingType.HOTEL,
        Cached_Item_ID=cache_row.Hotel_Cache_ID,
        Total_Price=body.hotel.total_price,
        Currency=body.hotel.currency,
        Notes=body.notes,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_to_response(db, booking)


@router.post(
    "/attractions",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attraction booking",
    description="Snapshots an attraction into AttractionCache and creates a tenant-scoped Booking row.",
)
def create_attraction_booking(
    body: CreateAttractionBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    cache_row = _cache_attraction(db, body.attraction)
    booking = Booking(
        User_ID=current_user.User_ID,
        Tenant_ID=current_tenant.Tenant_ID,
        Booking_Type=BookingType.ATTRACTION,
        Cached_Item_ID=cache_row.Attraction_Cache_ID,
        Total_Price=body.attraction.price,
        Currency=body.attraction.currency,
        Notes=body.notes,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return _booking_to_response(db, booking)

# ============================================================================
# GET /bookings/by-agent-user — Task #22
# ============================================================================

@router.get(
    "/by-agent-user",
    response_model=list[BookingResponse],
    summary="Get all bookings for the current user",
    description=(
        "Returns every booking belonging to the authenticated user, scoped to "
        "their tenant. A user from Tenant A will never see Tenant B bookings "
        "(US-4 AC 4.2 tenant isolation)."
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
    return [_booking_to_response(db, b) for b in bookings]


# ============================================================================
# State machine — which status transitions are allowed?
# ============================================================================

# PENDING is the entry state. CANCELLED is terminal.
# CONFIRMED can still be CANCELLED (e.g. refund). CONFIRMED cannot go back to PENDING.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PENDING":   {"CONFIRMED", "CANCELLED"},
    "CONFIRMED": {"CANCELLED"},
    "CANCELLED": set(),  # terminal — nothing allowed
}


def _is_valid_transition(current: str, new: str) -> bool:
    """Check whether moving from current → new is allowed by the state machine."""
    if current == new:
        return True  # No-op is always allowed (idempotent updates)
    allowed = _ALLOWED_TRANSITIONS.get(current, set())
    return new in allowed


# ============================================================================
# PUT /bookings/{id} — update status
# ============================================================================

@router.put(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Update a booking's status",
    description=(
        "Updates a booking's status, enforcing the lifecycle state machine "
        "(PENDING → CONFIRMED → CANCELLED). Tenant-scoped: a user from "
        "Tenant A receives 404 (not 403) if they target Tenant B's booking, "
        "to prevent cross-tenant information disclosure (TC-07 / AC 4.2)."
    ),
    responses={
        200: {"description": "Status updated."},
        401: {"description": "JWT missing or invalid."},
        404: {"description": "Booking not found in this tenant."},
        422: {"description": "Illegal status transition or validation error."},
    },
)
def update_booking_status(
    booking_id: int,
    body: UpdateBookingStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    # Tenant-scoped query — returns 404 if the booking is in a different tenant.
    booking = (
        db.query(Booking)
        .filter(
            Booking.Booking_ID == booking_id,
            Booking.Tenant_ID == current_tenant.Tenant_ID,
        )
        .first()
    )

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found.",
        )

    # Validate the state transition.
    current_status_value = (
        booking.Status.value if hasattr(booking.Status, "value") else str(booking.Status)
    )
    if not _is_valid_transition(current_status_value, body.status):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Cannot transition booking from {current_status_value} to {body.status}. "
                f"Allowed transitions from {current_status_value}: "
                f"{sorted(_ALLOWED_TRANSITIONS.get(current_status_value, set())) or 'none (terminal state)'}."
            ),
        )

    # Apply the update.
    booking.Status = body.status
    db.commit()
    db.refresh(booking)

    return _booking_to_response(db, booking)


# ============================================================================
# PATCH /bookings/{id}/cancel — Task #24
# ============================================================================

@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Cancel a booking",
    description=(
        "Sets the booking status to CANCELLED. Idempotent — cancelling an "
        "already-cancelled booking returns 200. Tenant-scoped: users can only "
        "cancel their own bookings within their tenant (returns 404 otherwise)."
    ),
    responses={
        200: {"description": "Booking cancelled (or was already cancelled)."},
        401: {"description": "Missing or invalid JWT."},
        404: {"description": "Booking not found or belongs to a different tenant/user."},
    },
)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: Tenant = Depends(get_current_tenant),
) -> BookingResponse:
    booking = (
        db.query(Booking)
        .filter(
            Booking.Booking_ID == booking_id,
            Booking.User_ID == current_user.User_ID,
            Booking.Tenant_ID == current_tenant.Tenant_ID,
        )
        .first()
    )
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    booking.Status = "CANCELLED"
    db.commit()
    db.refresh(booking)
    return _booking_to_response(db, booking)