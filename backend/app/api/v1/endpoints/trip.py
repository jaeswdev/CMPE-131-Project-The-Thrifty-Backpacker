"""
POST /api/v1/trip/calculate — stateless trip budget calculator.

US-3: Trip-total budget widget. Returns a green/yellow/red traffic-light
status so the Phase 3 UI can show whether the user's selections fit their budget.
"""

from fastapi import APIRouter

from app.schemas.trip import TripBreakdown, TripCalculateRequest, TripCalculateResponse

router = APIRouter()

# Status thresholds (Phase 1 AC 3)
_GREEN_THRESHOLD = 0.90   # <= 90% of budget -> green
_YELLOW_THRESHOLD = 1.00  # <= 100% of budget -> yellow, else red


def _classify(total: float, budget: float) -> tuple[str, str]:
    ratio = total / budget
    if ratio <= _GREEN_THRESHOLD:
        return "green", "Under budget — explore more!"
    if ratio <= _YELLOW_THRESHOLD:
        return "yellow", "Within budget — but cutting it close."
    return "red", "Over budget — adjust selections."


@router.post(
    "/calculate",
    response_model=TripCalculateResponse,
    summary="Calculate trip total and budget status",
    description=(
        "Accepts a budget and a breakdown of flight, hotel, and activity costs. "
        "Returns the total spent, amount remaining, percentage of budget used, "
        "and a green/yellow/red traffic-light status per US-3 AC 3."
    ),
    responses={
        200: {"description": "Budget calculation result with status"},
        422: {"description": "Validation error — invalid budget, negative cost, or bad currency code"},
    },
)
def calculate_trip_total(body: TripCalculateRequest) -> TripCalculateResponse:
    flights = body.flight_cost
    hotels = body.hotel_cost
    activities = sum(body.activity_costs)
    total = round(flights + hotels + activities, 2)

    remaining = round(body.budget - total, 2)
    percent_used = round((total / body.budget) * 100, 2)

    status, status_message = _classify(total, body.budget)

    return TripCalculateResponse(
        budget=body.budget,
        currency=body.currency,
        breakdown=TripBreakdown(
            flights=flights,
            hotels=hotels,
            activities=activities,
            total=total,
        ),
        remaining=remaining,
        percent_used=percent_used,
        status=status,
        status_message=status_message,
    )
