"""Request/response shapes for places, images and scans."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

PLACE_TYPE_PATTERN = "^(monument|museum|activity|food|nature)$"


class PlaceIn(BaseModel):
    city_id: int = Field(examples=[2])
    name: str = Field(min_length=2, max_length=160, examples=["Medinet Habu"])
    type: str = Field(pattern=PLACE_TYPE_PATTERN, examples=["monument"])
    short_description: str | None = Field(default=None, examples=["Mortuary temple of Ramesses III on the West Bank."])
    verified_info: str | None = Field(
        default=None, description="Checked history shown on the camera screen. The only source /ask answers from."
    )
    source_url: str | None = Field(default=None, examples=["https://en.wikipedia.org/wiki/Medinet_Habu_(temple)"])
    era: str | None = Field(default=None, max_length=80, examples=["New Kingdom, 20th Dynasty"])
    opening_hours: str | None = Field(default=None, max_length=120)
    ticket_price: int | None = Field(default=None, ge=0, description="Whole EGP")
    visit_minutes: int | None = Field(default=None, ge=5, le=600, examples=[90])
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    image_url: str | None = None
    recognition_label: str | None = Field(
        default=None,
        max_length=80,
        pattern="^[a-z0-9_]+$",
        description="Class name the vision model returns, lowercase with underscores",
        examples=["medinet_habu"],
    )
    interest_ids: list[int] = Field(default=[], examples=[[1, 8]])


class PlaceUpdateIn(BaseModel):
    """Every field is optional. Only the fields you send are changed."""

    city_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=160)
    type: str | None = Field(default=None, pattern=PLACE_TYPE_PATTERN)
    short_description: str | None = None
    verified_info: str | None = None
    source_url: str | None = None
    era: str | None = Field(default=None, max_length=80)
    opening_hours: str | None = Field(default=None, max_length=120)
    ticket_price: int | None = Field(default=None, ge=0)
    visit_minutes: int | None = Field(default=None, ge=5, le=600)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    image_url: str | None = None
    recognition_label: str | None = Field(default=None, max_length=80, pattern="^[a-z0-9_]+$")
    interest_ids: list[int] | None = Field(default=None, description="Replaces the whole list when sent")


class PlaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    name: str
    type: str
    short_description: str | None
    verified_info: str | None
    source_url: str | None
    era: str | None
    opening_hours: str | None
    ticket_price: int | None
    visit_minutes: int | None
    lat: float | None
    lng: float | None
    image_url: str | None
    recognition_label: str | None
    interest_ids: list[int]


class PlaceImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    place_id: int
    image_url: str
    source: str
    used_for_training: bool
    created_at: datetime


class PlaceDetailOut(PlaceOut):
    city_name: str
    images: list[PlaceImageOut]


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class LabelScanIn(BaseModel):
    place_id: int
    add_to_training: bool = True
