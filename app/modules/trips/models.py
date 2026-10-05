"""Tables: trips, trip_interests, trip_cities, trip_days, trip_items. Owner: Person 2."""

from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

BUDGET_LEVELS = ("low", "mid", "high")
TRIP_STATUSES = ("draft", "saved")
ITEM_TYPES = ("visit", "meal", "transport", "free_time")


class Trip(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "trips"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    start_date: Mapped[date | None] = mapped_column(Date)
    days: Mapped[int] = mapped_column(Integer)
    budget_level: Mapped[str] = mapped_column(Enum(*BUDGET_LEVELS, name="budget_level"))
    budget_total: Mapped[int | None] = mapped_column(Integer)
    suggest_destinations: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    status: Mapped[str] = mapped_column(
        Enum(*TRIP_STATUSES, name="trip_status"), default="draft", server_default="draft"
    )
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    total_cost: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TripInterest(Base):
    __tablename__ = "trip_interests"

    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[int] = mapped_column(ForeignKey("interests.id"), primary_key=True)


class TripCity(Base):
    __tablename__ = "trip_cities"

    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class TripDay(IdMixin, Base):
    __tablename__ = "trip_days"
    __table_args__ = (UniqueConstraint("trip_id", "day_number", name="uq_trip_day_number"),)

    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    # The hotel offer chosen for that night (Person 6 sets it when the traveler picks an offer).
    offer_id: Mapped[int | None] = mapped_column(ForeignKey("offers.id", ondelete="SET NULL"))
    title: Mapped[str | None] = mapped_column(String(160))


class TripItem(IdMixin, Base):
    __tablename__ = "trip_items"

    trip_day_id: Mapped[int] = mapped_column(ForeignKey("trip_days.id", ondelete="CASCADE"), index=True)
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    type: Mapped[str] = mapped_column(Enum(*ITEM_TYPES, name="trip_item_type"), default="visit")
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    note: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    position: Mapped[int] = mapped_column(Integer, default=0)
