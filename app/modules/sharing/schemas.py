"""Response shapes for summary and sharing. Owner: Person 3."""

from datetime import date, datetime

from pydantic import BaseModel

from app.modules.trips.schemas import TripCityOut, TripDayOut


class CostSplit(BaseModel):
    hotels: int
    tickets: int  # visits
    other: int  # meals, transport, free time
    total: int


class CitySummary(BaseModel):
    city_id: int
    city_name: str
    days: int
    costs: CostSplit


class HotelBooking(BaseModel):
    """One line per hotel offer to book, with the nights grouped."""

    offer_id: int
    hotel_name: str
    company_id: int
    company_name: str
    room_type: str
    nights: int
    first_night: date | None
    price_per_night: int
    subtotal: int
    free_cancellation: bool
    breakfast_included: bool


class DaySummary(BaseModel):
    day_number: int
    date: date | None
    city_name: str
    hotel_name: str | None
    visits: int
    costs: CostSplit


class SummaryOut(BaseModel):
    trip_id: int
    title: str
    status: str
    start_date: date | None
    end_date: date | None
    days: int
    nights_with_hotel: int
    places_count: int
    costs: CostSplit
    budget_total: int | None
    remaining: int | None  # budget_total - total; negative when over budget
    over_budget: bool
    cities: list[CitySummary]
    hotels: list[HotelBooking]
    per_day: list[DaySummary]
    is_shared: bool
    share_token: str | None


class ShareOut(BaseModel):
    share_token: str
    share_path: str  # front-end route to open, e.g. /shared/AbC...


class SharedTripOut(BaseModel):
    """Read-only view for people with the link. No budget, owner or ids for editing."""

    title: str
    start_date: date | None
    end_date: date | None
    days: int
    cities: list[TripCityOut]
    total_cost: int
    itinerary: list[TripDayOut]
    updated_at: datetime
