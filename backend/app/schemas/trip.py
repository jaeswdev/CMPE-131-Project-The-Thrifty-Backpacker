"""
Pydantic schemas for the trip total calculator.

Stateless request/response — no DB, no external calls.
The Phase 3 UI sends back prices it already has from search results;
we return a budget status so the UI can render the traffic-light widget.
"""

import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")

_NonNegFloat = Annotated[float, Field(ge=0)]


class TripCalculateRequest(BaseModel):
    budget: float = Field(..., gt=0, le=100_000, description="Total trip budget (1–100,000)")
    flight_cost: _NonNegFloat = Field(default=0.0, description="Sum of selected flight prices")
    hotel_cost: _NonNegFloat = Field(default=0.0, description="Sum of selected hotel prices")
    activity_costs: list[_NonNegFloat] = Field(default_factory=list, description="Individual activity prices")
    currency: str = Field(default="USD", description="ISO 4217 currency code (e.g. USD, EUR, GBP)")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not CURRENCY_PATTERN.match(v):
            raise ValueError("currency must be exactly 3 uppercase letters (e.g. USD)")
        return v


class TripBreakdown(BaseModel):
    flights: float
    hotels: float
    activities: float
    total: float


class TripCalculateResponse(BaseModel):
    budget: float
    currency: str
    breakdown: TripBreakdown
    remaining: float
    percent_used: float
    status: str           # "green" | "yellow" | "red"
    status_message: str
