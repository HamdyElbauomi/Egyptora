"""Request/response shapes for cities and interests."""

from pydantic import BaseModel, ConfigDict, Field


class CityIn(BaseModel):
    name: str = Field(min_length=2, max_length=80, examples=["Alexandria"])
    description: str | None = Field(default=None, examples=["Mediterranean city founded by Alexander the Great."])
    lat: float | None = Field(default=None, ge=-90, le=90, examples=[31.2001])
    lng: float | None = Field(default=None, ge=-180, le=180, examples=[29.9187])
    image_url: str | None = None


class CityUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    image_url: str | None = None


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    lat: float | None
    lng: float | None
    image_url: str | None


class CityCardOut(CityOut):
    """A destination card on preference step 4."""

    places_count: int


class InterestIn(BaseModel):
    name: str = Field(min_length=2, max_length=60, examples=["Diving"])
    icon: str | None = Field(default=None, max_length=60, examples=["waves"])


class InterestUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=60)
    icon: str | None = Field(default=None, max_length=60)


class InterestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None


class CitySuggestion(BaseModel):
    city: CityOut
    matching_places: int = Field(description="Places in this city that match at least one chosen interest")
    selected: bool = Field(description="True for the cities we recommend pre-selecting")


class SuggestOut(BaseModel):
    recommended_count: int = Field(description="How many cities fit the trip length")
    suggestions: list[CitySuggestion]
