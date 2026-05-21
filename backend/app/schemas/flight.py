"""
Pydantic schemas for flight search.

The shapes here are our PUBLIC contract — what Phase 3 UI sees.
They're deliberately decoupled from Tipsters' raw response shape so
we can swap providers later without breaking the frontend.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# === Inputs ===

class FlightAirport(BaseModel):
    """A single airport reference inside a FlightResult."""
    airport_code: str        # "SFO"
    airport_name: str        # "San Francisco International Airport"
    city: str                # "San Francisco"
    datetime: datetime       # ISO 8601 with timezone


# === Output items ===

class FlightResult(BaseModel):
    """One flight option returned to the UI."""
    offer_token: str                    # Opaque; used later by booking endpoint
    price_usd: float                    # Total price for the trip (all travelers)
    currency: str = "USD"
    airline_name: str                   # "JetBlue"
    airline_code: str                   # "B6"
    airline_logo_url: str | None = None
    stops: int                          # 0 = direct, 1 = one stop, etc.
    duration_minutes: int               # Total journey time (incl. layovers)
    departure: FlightAirport
    arrival: FlightAirport
    trip_type: str = "ONEWAY"           # ONEWAY | ROUNDTRIP
    # Return leg — set only for ROUNDTRIP offers
    return_departure: FlightAirport | None = None
    return_arrival: FlightAirport | None = None
    return_duration_minutes: int | None = None
    return_stops: int | None = None


class FlightSearchResponse(BaseModel):
    """Envelope returned by GET /api/v1/flights/search."""
    total_results: int
    currency: str = "USD"
    budget_filter_applied: bool         # True if we filtered out over-budget items
    items: list[FlightResult]
    message: str | None = None          # Set when items is empty (AC 1.4)