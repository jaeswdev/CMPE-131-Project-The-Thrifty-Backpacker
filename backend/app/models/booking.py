"""
Booking ORM model.

A single table that stores all bookings (flights, hotels, attractions) using
a discriminator pattern (Booking_Type) and a pointer (Cached_Item_ID) to
the appropriate cache table (FlightCache, HotelCache, or AttractionCache —
defined in Task #20).

Per Phase 1 US-4 AC 4.2, every booking carries a Tenant_ID so queries can be
scoped to the requesting tenant — preventing TC-07 cross-tenant leakage.
"""

import enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.base import Base


class BookingType(str, enum.Enum):
    """Discriminator for which kind of item this booking refers to."""
    FLIGHT = "FLIGHT"
    HOTEL = "HOTEL"
    ATTRACTION = "ATTRACTION"


class BookingStatus(str, enum.Enum):
    """Booking lifecycle states."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Booking(Base):
    __tablename__ = "Bookings"

    Booking_ID = Column(Integer, primary_key=True, autoincrement=True, index=True)

    # Who owns the booking.
    User_ID = Column(
        Integer,
        ForeignKey("Users.User_ID"),
        nullable=False,
        index=True,
    )

    # Multi-tenancy: which agency this booking belongs to.
    # Critical for AC 4.2 isolation — every query in /bookings endpoints
    # must filter by both User_ID AND Tenant_ID.
    Tenant_ID = Column(
        Integer,
        ForeignKey("Tenants.Tenant_ID"),
        nullable=False,
        index=True,
    )

    # Discriminator + pointer to the cache table that holds item details.
    # The actual FK constraint to FlightCache/HotelCache/AttractionCache is
    # NOT enforced at the DB level (SQLAlchemy can't FK to multiple tables);
    # the endpoint layer is responsible for validating Cached_Item_ID against
    # the appropriate table based on Booking_Type.
    Booking_Type = Column(
        Enum(BookingType, name="booking_type_enum"),
        nullable=False,
    )
    Cached_Item_ID = Column(Integer, nullable=False)

    # Lifecycle.
    Status = Column(
        Enum(BookingStatus, name="booking_status_enum"),
        nullable=False,
        default=BookingStatus.PENDING,
    )

    # Pricing snapshot at booking time (in case the upstream provider's
    # price changes later).
    Total_Price = Column(Float, nullable=False)
    Currency = Column(String(3), nullable=False, default="USD")

    # Optional free-form notes from the user.
    Notes = Column(Text, nullable=True)

    # Timestamps.
    Created_At = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    Updated_At = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<Booking(Booking_ID={self.Booking_ID}, User_ID={self.User_ID}, "
            f"Type={self.Booking_Type}, Status={self.Status})>"
        )