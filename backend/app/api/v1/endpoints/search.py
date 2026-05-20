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
from app.schemas.hotel import HotelResult, HotelSearchResponse

from app.services.rapidapi import (
    resolve_flight_location, 
    resolve_hotel_location,
    search_flights_raw,
    search_hotels_raw,
)
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
    

# ============================================================================
# Hotel search
# ============================================================================


@router.get(
    "/hotels/search",
    response_model=HotelSearchResponse,
    summary="Search for hotels within a budget",
    description=(
        "Searches Tipsters' Booking.com API for hotels at a destination for a "
        "given date range, then filters results by the user's total budget for "
        "the stay. Destination can be a city name (e.g. 'London', 'Prague')."
    ),
    responses={
        200: {"description": "Search completed (results may be empty — see message field)."},
        422: {"description": "Validation error (budget out of range, bad dates, etc.)."},
        502: {"description": "Travel data provider is unreachable or returned an error."},
        504: {"description": "Travel data provider timed out."},
    },
)
async def search_hotels(
    destination: str = Query(..., min_length=2, max_length=80,
                             description="City name (e.g. 'London')"),
    checkin_date: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    checkout_date: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    budget: float = Query(..., gt=0, le=MAX_BUDGET,
                          description=f"Total stay budget in USD (${MIN_BUDGET}-${MAX_BUDGET})"),
    adults: int = Query(1, ge=1, le=10, description="Number of adult guests"),
    rooms: int = Query(1, ge=1, le=5, description="Number of rooms"),
    order_by: str = Query("popularity",
                          pattern="^(popularity|price|review_score|class_descending|class_ascending|distance)$",
                          description="Sort order"),
):
    """Search hotels and filter by budget."""

    # === Step 1: Validate date range ===
    if checkout_date <= checkin_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="checkout_date must be after checkin_date.",
        )

    # === Step 2: Resolve destination → Tipsters dest_id + dest_type ===
    location = await resolve_hotel_location(destination)
    if location is None or not location.get("dest_id"):
        return HotelSearchResponse(
            total_results=0,
            location_label=destination,
            requested_currency="USD",
            budget_filter_applied=False,
            items=[],
            message=f"Could not find any destination matching '{destination}'.",
        )

    # === Step 3: Call Tipsters ===
    raw = await search_hotels_raw(
        dest_id=location["dest_id"],
        dest_type=location["dest_type"],
        checkin_date=checkin_date.isoformat(),
        checkout_date=checkout_date.isoformat(),
        adults=adults,
        room_number=rooms,
        currency="USD",
        order_by=order_by,
    )

    raw_results = raw.get("result", []) or []
    total_results_unfiltered = raw.get("count", len(raw_results))

    # === Step 4: Transform ===
    all_items: list[HotelResult] = []
    returned_currencies: set[str] = set()
    for hotel in raw_results:
        transformed = _transform_hotel(hotel)
        if transformed is not None:
            all_items.append(transformed)
            returned_currencies.add(transformed.currency)

    # === Step 5: Decide if we can filter by budget ===
    # Tipsters sometimes ignores filter_by_currency=USD and returns local currency.
    # We only filter if everything came back in USD.
    can_filter = (returned_currencies == {"USD"})

    if can_filter:
        under_budget = [item for item in all_items if item.total_price <= budget]
    else:
        # Currency drift detected — return all results, can't safely filter
        under_budget = all_items

    # === Step 6: Empty-results handling ===
    if not under_budget:
        if all_items and can_filter:
            cheapest = min(item.total_price for item in all_items)
            message = f"No hotels found within ${budget:,.0f}. Cheapest option is ${cheapest:,.2f}."
        else:
            message = f"No hotels found in {location['label']} for those dates."
        return HotelSearchResponse(
            total_results=total_results_unfiltered,
            location_label=location["label"],
            requested_currency="USD",
            budget_filter_applied=can_filter,
            items=[],
            message=message,
        )

    response_message = None
    if not can_filter:
        currencies_str = ", ".join(sorted(returned_currencies))
        response_message = (
            f"Note: hotels are priced in {currencies_str} (provider did not honor USD request). "
            "Budget filter was not applied — please review prices carefully."
        )

    return HotelSearchResponse(
        total_results=total_results_unfiltered,
        location_label=location["label"],
        requested_currency="USD",
        budget_filter_applied=can_filter,
        items=under_budget,
        message=response_message,
    )


def _transform_hotel(hotel: dict[str, Any]) -> HotelResult | None:
    """Convert one Tipsters hotel dict into a HotelResult. Returns None if malformed."""
    try:
        hotel_id = hotel.get("hotel_id")
        if not hotel_id:
            return None

        # Price extraction — Tipsters uses composite_price_breakdown
        price_block = hotel.get("composite_price_breakdown") or {}
        gross_total = price_block.get("gross_amount") or {}
        gross_per_night = price_block.get("gross_amount_per_night") or {}

        total_price = gross_total.get("value")
        if total_price is None:
            # No usable price — skip this result
            return None

        currency = gross_total.get("currency") or hotel.get("currencycode") or "USD"

        # Distance comes as a string ("5.65")
        distance_str = hotel.get("distance_to_cc")
        try:
            distance_km = float(distance_str) if distance_str else None
        except (ValueError, TypeError):
            distance_km = None

        return HotelResult(
            hotel_id=int(hotel_id),
            hotel_name=hotel.get("hotel_name", "Unknown"),
            accommodation_type=hotel.get("accommodation_type_name"),
            star_class=hotel.get("class"),
            total_price=float(total_price),
            price_per_night=float(gross_per_night.get("value")) if gross_per_night.get("value") is not None else None,
            currency=currency,
            review_score=hotel.get("review_score"),
            review_score_word=hotel.get("review_score_word"),
            review_count=hotel.get("review_nr"),
            city=hotel.get("city", "Unknown"),
            address=hotel.get("address"),
            distance_to_center_km=distance_km,
            latitude=hotel.get("latitude"),
            longitude=hotel.get("longitude"),
            photo_url=hotel.get("max_photo_url") or hotel.get("main_photo_url"),
            booking_url=hotel.get("url"),
        )
    except Exception:
        # Defensive: malformed hotel doesn't crash the whole response
        return None