"""Request/response shapes for hotels and search. Owner: Person 5."""

from pydantic import BaseModel, Field


class HotelIn(BaseModel):
    city_id: int
    name: str
    stars: int | None = Field(default=None, ge=1, le=5)
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    description: str | None = None
    amenities: list[str] = []
    image_url: str | None = None


class HotelUpdateIn(BaseModel):
    name: str | None = None
    stars: int | None = Field(default=None, ge=1, le=5)
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    description: str | None = None
    amenities: list[str] | None = None
    image_url: str | None = None


class HotelSearchIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    trip_id: int | None = None
    city_id: int | None = None


class FixSqlIn(BaseModel):
    sql: str
