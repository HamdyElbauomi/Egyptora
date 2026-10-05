"""Request/response shapes for trips. Owner: Person 2."""

from datetime import date, time

from pydantic import BaseModel, Field, model_validator


class GenerateTripIn(BaseModel):
    interest_ids: list[int] = Field(min_length=1)
    budget_level: str = Field(pattern="^(low|mid|high)$")
    budget_total: int | None = None
    days: int = Field(ge=1, le=21)
    start_date: date | None = None
    city_ids: list[int] = []
    suggest: bool = False

    @model_validator(mode="after")
    def cities_or_suggest(self):
        if not self.city_ids and not self.suggest:
            raise ValueError("Send city_ids or suggest=true")
        return self


class UpdateTripIn(BaseModel):
    title: str | None = None
    start_date: date | None = None
    days: int | None = Field(default=None, ge=1, le=21)


class AddItemIn(BaseModel):
    place_id: int | None = None
    type: str = Field(default="visit", pattern="^(visit|meal|transport|free_time)$")
    start_time: time | None = None
    end_time: time | None = None
    note: str | None = None
    cost: int = 0


class UpdateItemIn(BaseModel):
    start_time: time | None = None
    end_time: time | None = None
    note: str | None = None
    cost: int | None = None


class ReorderIn(BaseModel):
    item_ids: list[int]
