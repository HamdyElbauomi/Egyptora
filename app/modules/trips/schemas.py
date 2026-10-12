"""Request/response shapes for trips. Owner: Person 2."""

from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator


class GenerateTripIn(BaseModel):
    interest_ids: list[int] = Field(min_length=1)
    budget_level: str = Field(pattern="^(low|mid|high)$")
    budget_total: int | None = Field(default=None, ge=0, description="Whole trip budget in EGP (optional)")
    days: int = Field(ge=1, le=21)
    start_date: date | None = None
    city_ids: list[int] = Field(default=[], description="Chosen cities in visiting order")
    suggest: bool = Field(default=False, description="true = let Egyptora pick cities (when city_ids is empty)")

    @model_validator(mode="after")
    def cities_or_suggest(self):
        if not self.city_ids and not self.suggest:
            raise ValueError("Send city_ids or suggest=true")
        return self


class UpdateTripIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    start_date: date | None = None
    days: int | None = Field(default=None, ge=1, le=21)
    budget_total: int | None = Field(default=None, ge=0)


def _check_times(start: time | None, end: time | None) -> None:
    if start and end and end < start:
        raise ValueError("end_time must be after start_time")


class AddItemIn(BaseModel):
    place_id: int | None = None
    type: str = Field(default="visit", pattern="^(visit|meal|transport|free_time)$")
    start_time: time | None = Field(default=None, description="Empty = right after the day's last item")
    end_time: time | None = Field(default=None, description="Empty = start + the place's visit length")
    note: str | None = None
    cost: int | None = Field(default=None, ge=0, description="Empty = the place's ticket price")

    @model_validator(mode="after")
    def check(self):
        if self.type == "visit" and self.place_id is None:
            raise ValueError("A visit needs a place_id")
        _check_times(self.start_time, self.end_time)
        return self


class UpdateItemIn(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    note: str | None = None
    cost: int | None = Field(default=None, ge=0)


class ReorderIn(BaseModel):
    item_ids: list[int] = Field(description="Every item id of the day, in the new order")


class ChooseOfferIn(BaseModel):
    offer_id: int | None = Field(description="An offer from GET /hotels/{id}/offers, or null to remove the hotel")


# ---------- responses ----------


class TripItemOut(BaseModel):
    id: int
    place_id: int | None
    place_name: str | None
    place_image_url: str | None
    type: str
    start_time: time | None
    end_time: time | None
    note: str | None
    cost: int
    position: int


class DayHotelOut(BaseModel):
    offer_id: int
    hotel_id: int
    hotel_name: str
    stars: int | None
    company_id: int
    company_name: str
    room_type: str
    price_per_night: int
    free_cancellation: bool
    breakfast_included: bool


class TripDayOut(BaseModel):
    id: int
    day_number: int
    date: date | None
    city_id: int
    city_name: str
    title: str | None
    hotel: DayHotelOut | None
    items: list[TripItemOut]
    day_cost: int  # items + tonight's hotel


class TripCityOut(BaseModel):
    id: int
    name: str


class TripOut(BaseModel):
    id: int
    title: str
    status: str
    start_date: date | None
    end_date: date | None
    days: int
    budget_level: str
    budget_total: int | None
    total_cost: int
    over_budget: bool
    interest_ids: list[int]
    cities: list[TripCityOut]
    itinerary: list[TripDayOut]
    created_at: datetime
    updated_at: datetime


class TripCardOut(BaseModel):
    id: int
    title: str
    status: str
    start_date: date | None
    days: int
    cities: list[str]
    total_cost: int
    budget_total: int | None
    created_at: datetime
