"""Request/response shapes for hotels and search."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HotelIn(BaseModel):
    city_id: int = Field(examples=[2])
    name: str = Field(min_length=2, max_length=160, examples=["Theban Palms Hotel"])
    stars: int | None = Field(default=None, ge=1, le=5, examples=[4])
    address: str | None = Field(default=None, examples=["Corniche El Nile, Luxor"])
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    description: str | None = None
    amenities: list[str] = Field(default=[], examples=[["pool", "wifi", "nile view"]])
    image_url: str | None = None


class HotelUpdateIn(BaseModel):
    """Every field is optional. Only the fields you send are changed."""

    city_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=160)
    stars: int | None = Field(default=None, ge=1, le=5)
    address: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    description: str | None = None
    amenities: list[str] | None = None
    image_url: str | None = None


class HotelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    name: str
    stars: int | None
    address: str | None
    lat: float | None
    lng: float | None
    description: str | None
    amenities: list[str]
    image_url: str | None
    created_at: datetime


class HotelCardOut(HotelOut):
    """A hotel in a list or a detail page, with what its offers look like right now."""

    city_name: str
    min_price: int | None = Field(description="Lowest active offer per night, EGP. Null when no offers yet")
    offers_count: int = Field(description="Active offers from all companies")


class ImportRowError(BaseModel):
    row: int = Field(description="Line number in the CSV, counting the header as line 1")
    error: str


class ImportOut(BaseModel):
    created: int
    skipped: int = Field(description="Rows for hotels that already exist (same name in the same city)")
    skipped_names: list[str]


class HotelSearchIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    trip_id: int | None = None
    city_id: int | None = None


class FixSqlIn(BaseModel):
    sql: str
