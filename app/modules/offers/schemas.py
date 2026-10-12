"""Request/response shapes for offers, market position and alerts."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.companies.schemas import CompanyPublicOut


class _Dates(BaseModel):
    @model_validator(mode="after")
    def dates_in_order(self):
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise ValueError("valid_to must be on or after valid_from")
        return self


class OfferIn(_Dates):
    hotel_id: int = Field(examples=[5])
    room_type: str = Field(min_length=2, max_length=60, examples=["Double"])
    price_per_night: int = Field(gt=0, le=1_000_000, description="Whole EGP", examples=[1250])
    breakfast_included: bool = False
    free_cancellation: bool = False
    cancellation_days: int | None = Field(
        default=None, ge=0, le=60, description="Free cancellation until this many days before arrival"
    )
    valid_from: date | None = None
    valid_to: date | None = None


class OfferUpdateIn(_Dates):
    """Only the fields you send are changed."""

    room_type: str | None = Field(default=None, min_length=2, max_length=60)
    price_per_night: int | None = Field(default=None, gt=0, le=1_000_000)
    breakfast_included: bool | None = None
    free_cancellation: bool | None = None
    cancellation_days: int | None = Field(default=None, ge=0, le=60)
    valid_from: date | None = None
    valid_to: date | None = None


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hotel_id: int
    company_id: int
    room_type: str
    price_per_night: int
    breakfast_included: bool
    free_cancellation: bool
    cancellation_days: int | None
    valid_from: date | None
    valid_to: date | None
    status: str
    flag_reason: str | None
    created_at: datetime
    updated_at: datetime


class MyOfferOut(OfferOut):
    """An offer in the company portal, with where it stands against competitors."""

    hotel_name: str
    city_name: str
    position: int | None = Field(description="1 = cheapest among active offers for the same hotel and room type")
    competitors: int = Field(description="How many active offers compete for the same hotel and room type")
    lowest_price: int | None


class CompetitorOut(BaseModel):
    company_name: str
    price_per_night: int
    free_cancellation: bool
    breakfast_included: bool
    trust_score: float | None
    is_mine: bool


class MarketOut(BaseModel):
    offer_id: int
    hotel_name: str
    room_type: str
    my_price: int
    position: int | None = Field(description="Null when the offer isn't active")
    total: int = Field(description="Active offers for this hotel and room type, mine included")
    lowest_price: int
    gap_to_lowest: int = Field(description="EGP above the lowest price (0 when I'm the cheapest)")
    best_value_rank: int | None
    competitors: list[CompetitorOut]


class DashboardOut(BaseModel):
    status: str
    trust_score: float | None
    reviews_count: int
    active_offers: int
    paused_offers: int
    flagged_offers: int
    cheapest_in_market: int = Field(description="Active offers where I have the lowest price")
    times_chosen: int = Field(description="Trip nights where travelers picked one of my offers")
    unread_alerts: int


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    offer_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime


class OfferImportOut(BaseModel):
    created: int
    updated: int


class AdminOfferOut(OfferOut):
    hotel_name: str
    company_name: str
    market_median: int | None = Field(description="Median active price for the same hotel and room type")
    price_check: str | None = Field(description='"low" when the price is under half the median: worth a look')


class FlagIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500, examples=["Price is a fifth of every other offer."])


class PublicOfferOut(BaseModel):
    """One company's offer on the hotel page."""

    offer_id: int
    room_type: str
    price_per_night: int
    breakfast_included: bool
    free_cancellation: bool
    cancellation_days: int | None
    valid_to: date | None
    company: CompanyPublicOut
    is_lowest: bool
    is_best_value: bool


class HotelOffersOut(BaseModel):
    hotel_id: int
    hotel_name: str
    offers: list[PublicOfferOut]


class ChooseOfferIn(BaseModel):
    offer_id: int | None = Field(description="Null removes the hotel from that night")
