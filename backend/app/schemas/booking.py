"""
Pydantic schemas for the Bookings resource.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.booking import BookingStatus, BookingType


class BookingResponse(BaseModel):
    Booking_ID: int
    User_ID: int
    Tenant_ID: int
    Booking_Type: BookingType
    Cached_Item_ID: int
    Status: BookingStatus
    Total_Price: float
    Currency: str
    Notes: Optional[str]
    Created_At: datetime
    Updated_At: datetime

    model_config = {"from_attributes": True}
