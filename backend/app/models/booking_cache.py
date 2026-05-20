"""
Cache models — snapshots of bookable items at the moment of booking.

When a user books a flight/hotel/attraction, we snapshot the relevant fields
from the search response into one of these tables. The Booking row then
points to the cache row by ID via Cached_Item_ID.

Why we cache:
- Tipsters' inventory rolls forward. The exact offer the user booked may
  disappear within hours; we can't re-fetch it for the confirmation page.
- Booking confirmations should remain renderable forever, independent of
  what the upstream API does.

No FK from cache to Booking: the relationship is logical only. Booking.Cached_Item_ID
points to a row in whichever cache table matches Booking.Booking_Type.
Endpoint code (Task #21) is responsible for keeping these in sync.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.base import Base


# ============================================================================
# Flights
# ============================================================================

class FlightCache(Base):
    """Snapshot of a flight offer at booking time."""
    __tablename__ = "FlightCache"

    Flight_Cache_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Opaque token from Tipsters — needed if we ever re-validate the offer.
    Offer_Token = Column(Text, nullable=False)

    # Airline info.
    Airline_Name = Column(String(100), nullable=False)
    Airline_Code = Column(String(10), nullable=False)
    Airline_Logo_URL = Column(String(500), nullable=True)

    # Departure.
    Departure_Airport_Code = Column(String(10), nullable=False)
    Departure_Airport_Name = Column(String(200), nullable=False)
    Departure_City = Column(String(100), nullable=False)
    Departure_Datetime = Column(DateTime(timezone=True), nullable=False)

    # Arrival.
    Arrival_Airport_Code = Column(String(10), nullable=False)
    Arrival_Airport_Name = Column(String(200), nullable=False)
    Arrival_City = Column(String(100), nullable=False)
    Arrival_Datetime = Column(DateTime(timezone=True), nullable=False)

    # Journey details.
    Stops = Column(Integer, nullable=False, default=0)
    Duration_Minutes = Column(Integer, nullable=False)
    Trip_Type = Column(String(20), nullable=False, default="ONEWAY")

    # Price snapshot.
    Price = Column(Float, nullable=False)
    Currency = Column(String(3), nullable=False, default="USD")

    Created_At = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<FlightCache(ID={self.Flight_Cache_ID}, {self.Airline_Code} "
            f"{self.Departure_Airport_Code}→{self.Arrival_Airport_Code}, "
            f"{self.Price} {self.Currency})>"
        )


# ============================================================================
# Hotels
# ============================================================================

class HotelCache(Base):
    """Snapshot of a hotel listing at booking time."""
    __tablename__ = "HotelCache"

    Hotel_Cache_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Tipsters' own hotel ID — used if we need to re-fetch live availability.
    External_Hotel_ID = Column(Integer, nullable=False)

    Hotel_Name = Column(String(200), nullable=False)
    Accommodation_Type = Column(String(50), nullable=True)
    Star_Class = Column(Integer, nullable=True)

    City = Column(String(100), nullable=False)
    Address = Column(String(500), nullable=True)

    # Stay window.
    Checkin_Date = Column(Date, nullable=False)
    Checkout_Date = Column(Date, nullable=False)

    # Price snapshot.
    Total_Price = Column(Float, nullable=False)
    Price_Per_Night = Column(Float, nullable=True)
    Currency = Column(String(3), nullable=False, default="USD")

    Photo_URL = Column(String(500), nullable=True)
    Booking_URL = Column(String(500), nullable=True)

    Created_At = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<HotelCache(ID={self.Hotel_Cache_ID}, {self.Hotel_Name} "
            f"in {self.City}, {self.Total_Price} {self.Currency})>"
        )


# ============================================================================
# Attractions
# ============================================================================

class AttractionCache(Base):
    """Snapshot of an attraction/activity at booking time."""
    __tablename__ = "AttractionCache"

    Attraction_Cache_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Tipsters' product ID — opaque string like "PRCMOkYUz7Um".
    Offer_Token = Column(String(100), nullable=False)

    Name = Column(String(300), nullable=False)
    Description = Column(Text, nullable=True)
    City = Column(String(100), nullable=True)

    # Price (per person).
    Price = Column(Float, nullable=False)
    Currency = Column(String(3), nullable=False, default="USD")

    # Rating snapshot.
    Rating = Column(Float, nullable=True)

    # Flags.
    Has_Free_Cancellation = Column(Boolean, nullable=False, default=False)

    # Availability window from the search.
    Start_Date = Column(Date, nullable=False)
    End_Date = Column(Date, nullable=False)

    Photo_URL = Column(String(500), nullable=True)
    Booking_URL = Column(String(500), nullable=True)

    Created_At = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<AttractionCache(ID={self.Attraction_Cache_ID}, {self.Name}, "
            f"{self.Price} {self.Currency})>"
        )