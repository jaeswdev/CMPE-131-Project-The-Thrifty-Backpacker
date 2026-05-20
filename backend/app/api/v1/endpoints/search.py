"""
Flight, hotel, and attraction search endpoints.

Currently implements GET /api/v1/flights/search for US-1 / AC 1.1-1.5.
Future PRs will add /hotels/search (Task #15) and /attractions/search (Task #16).
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.flight import (
    FlightAirport,
    FlightResult,
    FlightSearchResponse,
)
from app.services.rapidapi import resolve_flight_location, search_flights_raw

router = APIRouter()


# Per Phase 1 AC 1.1: budget range $1 to $100,000 USD.
MIN_BUDGET = 1
MAX_BUDGET = 100_000


@router.get(
    "/flights/search",
    response_model=FlightSearchResponse,
    summary="Search for flights within a budget",
    description=(
        "Searches Tipsters' Booking.com API for flights between two locations on a "
        "given date, then filters results by the user's total budget (US-1). "
        "Origins and destinations can be airport codes (e.g. 'SFO') or city names "
        "(e.g. 'London')."
    ),
    responses={
        200: {"description": "Search completed (results may be empty — see message field)."},
        422: {"description": "Validation error (budget out of range, bad date, etc.)."},
        502: {"description": "Travel data provider is unreachable or returned an error."},
        504: {"description": "Travel data provider timed out."},
    },
)
async def search_flights(
    origin: str = Query(..., min_length=2, max_length=50,
                        description="Airport code or city name (e.g. 'SFO' or 'San Francisco')"),
    destination: str = Query(..., min_length=2, max_length=50,
                             description="Airport code or city name (e.g. 'LHR' or 'London')"),
    depart_date: date = Query(...,
                              description="Departure date in YYYY-MM-DD format"),
    budget: float = Query(..., gt=0, le=MAX_BUDGET,
                          description=f"Total trip budget in USD (${MIN_BUDGET}-${MAX_BUDGET})"),
    adults: int = Query(1, ge=1, le=10, description="Number of adult travelers (1-10)"),
    cabin_class: str = Query("ECONOMY",
                             pattern="^(ECONOMY|PREMIUM_ECONOMY|BUSINESS|FIRST)$",
                             description="Cabin class"),
):
    """Search flights and filter by budget."""

    # === Step 1: Resolve user-friendly inputs → Tipsters internal codes ===
    from_code = await resolve_flight_location(origin)
    if from_code is None:
        return FlightSearchResponse(
            total_results=0,
            budget_filter_applied=False,
            items=[],
            message=f"Could not find any airport or city matching '{origin}'.",
        )

    to_code = await resolve_flight_location(destination)
    if to_code is None:
        return FlightSearchResponse(
            total_results=0,
            budget_filter_applied=False,
            items=[],
            message=f"Could not find any airport or city matching '{destination}'.",
        )

    # === Step 2: Call Tipsters ===
    raw = await search_flights_raw(
        from_code=from_code,
        to_code=to_code,
        depart_date=depart_date.isoformat(),
        adults=adults,
        cabin_class=cabin_class,
        currency="USD",
    )

    raw_offers = raw.get("flightOffers", []) or []
    total_results_unfiltered = (raw.get("aggregation") or {}).get("totalCount", len(raw_offers))

    # === Step 3: Transform raw Tipsters offers → our clean schema ===
    all_items: list[FlightResult] = []
    for offer in raw_offers:
        transformed = _transform_offer(offer)
        if transformed is not None:
            all_items.append(transformed)

    # === Step 4: Filter by budget (US-1 AC 1.2) ===
    under_budget = [item for item in all_items if item.price_usd <= budget]

    # === Step 5: Handle empty-results case (AC 1.4) ===
    if not under_budget:
        if all_items:
            message = f"No trips found within ${budget:,.0f}. Cheapest option is ${min(i.price_usd for i in all_items):,.2f}."
        else:
            message = f"No flights found from {origin} to {destination} on {depart_date}."
        return FlightSearchResponse(
            total_results=total_results_unfiltered,
            budget_filter_applied=True,
            items=[],
            message=message,
        )

    return FlightSearchResponse(
        total_results=total_results_unfiltered,
        budget_filter_applied=True,
        items=under_budget,
    )


# === Transformation helpers ===

def _money(money_obj: dict[str, Any] | None) -> float:
    """
    Tipsters returns prices as {currencyCode, units, nanos}.
    Real value = units + nanos/1e9. We round to 2 decimals for display.
    """
    if not money_obj:
        return 0.0
    units = money_obj.get("units") or 0
    nanos = money_obj.get("nanos") or 0
    return round(float(units) + float(nanos) / 1_000_000_000, 2)


def _transform_offer(offer: dict[str, Any]) -> FlightResult | None:
    """Convert one Tipsters flightOffer dict into a FlightResult. Returns None if malformed."""
    try:
        segments = offer.get("segments") or []
        if not segments:
            return None

        first_segment = segments[0]
        legs = first_segment.get("legs") or []
        if not legs:
            return None

        # Airline info from the first leg (multi-leg flights may have mixed carriers; we pick the first)
        carriers_data = legs[0].get("carriersData") or []
        if carriers_data:
            airline_name = carriers_data[0].get("name", "Unknown")
            airline_code = carriers_data[0].get("code", "??")
            airline_logo_url = carriers_data[0].get("logo")
        else:
            airline_name = "Unknown"
            airline_code = "??"
            airline_logo_url = None

        # Stops = number of legs minus 1 (1 leg = direct, 2 legs = 1 stop, etc.)
        stops = max(0, len(legs) - 1)

        # Total journey time is provided in SECONDS by Tipsters
        duration_seconds = first_segment.get("totalTime", 0) or 0
        duration_minutes = int(duration_seconds // 60)

        dep_airport = first_segment.get("departureAirport") or {}
        arr_airport = first_segment.get("arrivalAirport") or {}

        return FlightResult(
            offer_token=offer.get("token", ""),
            price_usd=_money(offer.get("priceBreakdown", {}).get("total")),
            currency=offer.get("priceBreakdown", {}).get("total", {}).get("currencyCode", "USD"),
            airline_name=airline_name,
            airline_code=airline_code,
            airline_logo_url=airline_logo_url,
            stops=stops,
            duration_minutes=duration_minutes,
            departure=FlightAirport(
                airport_code=dep_airport.get("code", "???"),
                airport_name=dep_airport.get("name", "Unknown"),
                city=dep_airport.get("cityName", "Unknown"),
                datetime=first_segment.get("departureTimeTz") or first_segment.get("departureTime"),
            ),
            arrival=FlightAirport(
                airport_code=arr_airport.get("code", "???"),
                airport_name=arr_airport.get("name", "Unknown"),
                city=arr_airport.get("cityName", "Unknown"),
                datetime=first_segment.get("arrivalTimeTz") or first_segment.get("arrivalTime"),
            ),
            trip_type=offer.get("tripType", "ONEWAY"),
        )
    except Exception:
        # Defensive: if Tipsters returns a malformed offer, skip it rather than crash the whole response
        return None