"""Request/response shapes for cities and interests. Owner: Person 3."""

from pydantic import BaseModel


class CityIn(BaseModel):
    name: str
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    image_url: str | None = None


class CityUpdateIn(BaseModel):
    name: str | None = None
    description: str | None = None
    lat: float | None = None
    lng: float | None = None
    image_url: str | None = None


class InterestIn(BaseModel):
    name: str
    icon: str | None = None


class InterestUpdateIn(BaseModel):
    name: str | None = None
    icon: str | None = None
