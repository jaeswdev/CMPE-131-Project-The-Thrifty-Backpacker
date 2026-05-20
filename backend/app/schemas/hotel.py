"""
Pydantic schemas for hotel search.

Shapes here are our PUBLIC contract — what Phase 3 UI sees. Decoupled
from Tipsters' raw schema so we can swap providers without breaking the UI.
"""

from pydantic import BaseModel, Field


class HotelResult(BaseModel):
    """One hotel option returned to the UI."""
    hotel_id: int                          # Tipsters internal ID (used as offer_token in bookings)
    hotel_name: str                        # "STAGES HOTEL Prague"
    accommodation_type: str | None = None  # "Hotel", "Hostel", "Apartment"
    star_class: int | None = None          # 0-5 (None if not rated)

    # Pricing
    total_price: float                     # Total for the stay (all nights)
    price_per_night: float | None = None   # Per-night rate
    currency: str                          # "USD", "CZK", etc. — TRUST THE API

    # Reviews
    review_score: float | None = None      # 0-10
    review_score_word: str | None = None   # "Superb", "Very good"
    review_count: int | None = None

    # Location
    city: str
    address: str | None = None
    distance_to_center_km: float | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Media + links
    photo_url: str | None = None
    booking_url: str | None = None


class HotelSearchResponse(BaseModel):
    """Envelope returned by GET /api/v1/hotels/search."""
    total_results: int
    location_label: str                    # Human-readable resolved location ("Prague, Czech Republic")
    requested_currency: str                # What the user asked for ("USD")
    budget_filter_applied: bool            # False if API returned non-USD prices
    items: list[HotelResult]
    message: str | None = None             # Set when items is empty