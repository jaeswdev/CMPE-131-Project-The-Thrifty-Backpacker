"""
Pydantic schemas for booking endpoints.

The request shape uses a discriminated union: clients send a booking_type
field plus the appropriate sub-payload (flight/hotel/attraction).

The response shape is unified — every booking has the same envelope fields
plus an `item` sub-object with the cached item's details.
"""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Request — Per-type item payloads
# ============================================================================

class FlightItemPayload(BaseModel):
    """Subset of FlightResult fields we cache when booking."""
    offer_token: str
    airline_name: str
    airline_code: str
    airline_logo_url: str | None = None
    departure_airport_code: str
    departure_airport_name: str
    departure_city: str
    departure_datetime: datetime
    arrival_airport_code: str
    arrival_airport_name: str
    arrival_city: str
    arrival_datetime: datetime
    stops: int = Field(0, ge=0)
    duration_minutes: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    currency: str = Field("USD", pattern="^[A-Z]{3}$")
    trip_type: str = "ONEWAY"


class HotelItemPayload(BaseModel):
    """Subset of HotelResult fields we cache when booking."""
    external_hotel_id: int
    hotel_name: str
    accommodation_type: str | None = None
    star_class: int | None = Field(None, ge=0, le=5)
    city: str
    address: str | None = None
    checkin_date: date
    checkout_date: date
    total_price: float = Field(..., gt=0)
    price_per_night: float | None = None
    currency: str = Field("USD", pattern="^[A-Z]{3}$")
    photo_url: str | None = None
    booking_url: str | None = None


class AttractionItemPayload(BaseModel):
    """Subset of AttractionResult fields we cache when booking."""
    offer_token: str
    name: str
    description: str | None = None
    city: str | None = None
    price: float = Field(..., gt=0)
    currency: str = Field("USD", pattern="^[A-Z]{3}$")
    rating: float | None = Field(None, ge=0, le=5)
    has_free_cancellation: bool = False
    start_date: date
    end_date: date
    photo_url: str | None = None
    booking_url: str | None = None


# ============================================================================
# Request — Top-level booking creation body
# ============================================================================

class CreateFlightBookingRequest(BaseModel):
    booking_type: Literal["FLIGHT"]
    flight: FlightItemPayload
    notes: str | None = Field(None, max_length=500)


class CreateHotelBookingRequest(BaseModel):
    booking_type: Literal["HOTEL"]
    hotel: HotelItemPayload
    notes: str | None = Field(None, max_length=500)


class CreateAttractionBookingRequest(BaseModel):
    booking_type: Literal["ATTRACTION"]
    attraction: AttractionItemPayload
    notes: str | None = Field(None, max_length=500)


# ============================================================================
# Response shape
# ============================================================================

class BookingResponse(BaseModel):
    """Unified booking response — every field a UI needs to render a confirmation."""
    Booking_ID: int
    User_ID: int
    Tenant_ID: int
    Booking_Type: str           # "FLIGHT" | "HOTEL" | "ATTRACTION"
    Cached_Item_ID: int
    Status: str                 # "PENDING" | "CONFIRMED" | "CANCELLED"
    Total_Price: float
    Currency: str
    Notes: str | None
    Created_At: datetime
    Updated_At: datetime

    # Cached item details — populated by the endpoint after JOIN with cache table.
    item: dict | None = None    # Shape depends on Booking_Type

    model_config = {"from_attributes": True}