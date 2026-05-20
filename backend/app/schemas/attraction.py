"""
Pydantic schemas for attractions search.

Powers US-2: free / low-cost activities for budget travelers like Violet.
Uses a price-tier filter (free / under_25 / 25_75 / 75_plus) instead of
a continuous budget — natural categories for how users actually think
about attractions.
"""

from pydantic import BaseModel


class AttractionResult(BaseModel):
    """One attraction option returned to the UI."""
    offer_token: str                       # Tipsters product ID
    name: str
    description: str | None = None
    price: float                           # Per-person price
    currency: str                          # "USD", "AED", "EUR", etc.

    # Reviews
    rating: float | None = None            # 0-5 scale
    review_count: int | None = None
    review_score_word: str | None = None   # "EXCEPTIONAL", "VERY_GOOD", etc.

    # Flags
    has_free_cancellation: bool = False
    is_bestseller: bool = False

    # Location
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    # Media + link
    photo_url: str | None = None
    booking_url: str | None = None


class AttractionSearchResponse(BaseModel):
    """Envelope returned by GET /api/v1/attractions/search."""
    total_results: int
    location_label: str
    requested_currency: str
    price_tier_applied: str | None = None  # Echo of the filter requested
    currency_filter_applied: bool          # False if API returned non-USD
    items: list[AttractionResult]
    message: str | None = None