"""Request/response shapes for places and scans. Owner: Person 4."""

from pydantic import BaseModel, Field


class PlaceIn(BaseModel):
    city_id: int
    name: str
    type: str = Field(pattern="^(monument|museum|activity|food|nature)$")
    short_description: str | None = None
    verified_info: str | None = None
    source_url: str | None = None
    era: str | None = None
    opening_hours: str | None = None
    ticket_price: int | None = None
    visit_minutes: int | None = None
    lat: float | None = None
    lng: float | None = None
    image_url: str | None = None
    recognition_label: str | None = None
    interest_ids: list[int] = []


class PlaceUpdateIn(BaseModel):
    name: str | None = None
    short_description: str | None = None
    verified_info: str | None = None
    source_url: str | None = None
    era: str | None = None
    opening_hours: str | None = None
    ticket_price: int | None = None
    visit_minutes: int | None = None
    image_url: str | None = None
    recognition_label: str | None = None
    interest_ids: list[int] | None = None


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class LabelScanIn(BaseModel):
    place_id: int
    add_to_training: bool = True
