"""Request/response shapes for offers. Owner: Person 6."""

from datetime import date

from pydantic import BaseModel, Field


class OfferIn(BaseModel):
    hotel_id: int
    room_type: str
    price_per_night: int = Field(gt=0, description="Whole EGP")
    breakfast_included: bool = False
    free_cancellation: bool = False
    cancellation_days: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class OfferUpdateIn(BaseModel):
    room_type: str | None = None
    price_per_night: int | None = Field(default=None, gt=0)
    breakfast_included: bool | None = None
    free_cancellation: bool | None = None
    cancellation_days: int | None = None
    valid_from: date | None = None
    valid_to: date | None = None


class FlagIn(BaseModel):
    reason: str


class ChooseOfferIn(BaseModel):
    offer_id: int
