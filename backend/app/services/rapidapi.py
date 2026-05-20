"""
RapidAPI Booking.com (Tipsters) HTTP client.

This module is the SINGLE place in the codebase that knows about RapidAPI.
Endpoints call functions defined here instead of crafting httpx calls
themselves. That way the auth headers, base URL, and timeout policy live
in exactly one place.

Future tasks (#15 hotels, #16 attractions) will add more functions here
following the same pattern as search_flights below.
"""

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


# Tipsters typically responds within 1-3 seconds. 10s is a generous ceiling
# that prevents our backend from hanging forever if their API is slow.
REQUEST_TIMEOUT_SECONDS = 10.0


def _default_headers() -> dict[str, str]:
    """Build the headers every RapidAPI request needs."""
    return {
        "x-rapidapi-key": settings.RAPIDAPI_KEY,
        "x-rapidapi-host": settings.RAPIDAPI_HOST,
        "Content-Type": "application/json",
    }


async def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Send a GET request to the RapidAPI Booking.com base URL.

    Raises HTTPException with a friendly message if the upstream API
    fails — endpoints don't need to handle httpx errors themselves.
    """
    url = f"{settings.RAPIDAPI_BASE_URL}{path}"

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, params=params, headers=_default_headers())
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Travel data provider timed out. Please try again.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach travel data provider: {exc.__class__.__name__}",
        )

    # 4xx/5xx from RapidAPI itself
    if response.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Travel data provider returned a server error.",
        )
    if response.status_code == 429:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Travel data provider rate limit reached. Please try again later.",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Travel data provider rejected the request (status={response.status_code}).",
        )

    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Travel data provider returned malformed JSON.",
        )


# === Location resolver ===

async def resolve_flight_location(query: str) -> str | None:
    """
    Convert a user-friendly query like "SFO" or "London" into Tipsters'
    internal location code like "SFO.AIRPORT" or "LON.CITY".

    Returns the location code string, or None if no location was found.

    Picking strategy:
      1. If any result's `short_code` matches the query exactly
         (case-insensitive), prefer that one — handles "SFO" → SFO airport.
      2. Otherwise prefer the first AIRPORT result.
      3. Otherwise fall back to the first result of any type.
    """
    query = query.strip()
    if not query:
        return None

    data = await _get(
        path="/v1/flights/locations",
        params={"name": query, "locale": "en-gb"},
    )

    # The response is a JSON array (list of location dicts)
    if not isinstance(data, list) or not data:
        return None

    # Strategy 1: exact short_code match
    query_upper = query.upper()
    for loc in data:
        if loc.get("short_code", "").upper() == query_upper:
            return loc.get("code")

    # Strategy 2: first AIRPORT result
    for loc in data:
        if loc.get("type") == "AIRPORT":
            return loc.get("code")

    # Strategy 3: first result of any type
    return data[0].get("code")


# === Flight search ===

async def search_flights_raw(
    from_code: str,
    to_code: str,
    depart_date: str,
    adults: int = 1,
    cabin_class: str = "ECONOMY",
    currency: str = "USD",
    flight_type: str = "ONEWAY",
    order_by: str = "BEST",
    return_date: str | None = None,
) -> dict[str, Any]:
    """
    Call Tipsters' flight search endpoint with already-resolved location codes.

    Returns the raw response dict. The transformation into our clean
    FlightResult schema happens in the endpoint layer, not here.

    `from_code` and `to_code` must already be in Tipsters' format
    (e.g. "SFO.AIRPORT", "LON.CITY"). Use resolve_flight_location() first.
    """
    params: dict[str, Any] = {
        "from_code": from_code,
        "to_code": to_code,
        "depart_date": depart_date,
        "adults": adults,
        "cabin_class": cabin_class,
        "currency": currency,
        "flight_type": flight_type,
        "order_by": order_by,
        "locale": "en-gb",
        "page_number": 0,
    }
    if return_date:
        params["return_date"] = return_date

    return await _get(path="/v1/flights/search", params=params)