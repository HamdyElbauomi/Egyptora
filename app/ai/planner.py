"""AI piece: trip planner agent. Owner: Person 2.

Why: decides which places go on which day, in what order, and which hotel offer fits the budget.
Then: POST /trips/generate saves the returned plan into trip_days and trip_items.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])


class CandidatePlace(BaseModel):
    place_id: int
    city_id: int
    name: str
    visit_minutes: int | None = None
    ticket_price: int | None = None
    interest_ids: list[int] = []


class CandidateOffer(BaseModel):
    offer_id: int
    city_id: int
    hotel_name: str
    price_per_night: int
    trust_score: float | None = None


class PlanIn(BaseModel):
    days: int
    budget_level: str
    budget_total: int | None = None
    interest_ids: list[int]
    city_ids: list[int]
    places: list[CandidatePlace]
    offers: list[CandidateOffer]


class PlannedItem(BaseModel):
    place_id: int | None
    type: str = "visit"
    start_time: str | None = None  # "09:00"
    end_time: str | None = None
    note: str | None = None
    cost: int = 0


class PlannedDay(BaseModel):
    day_number: int
    city_id: int
    title: str
    offer_id: int | None
    items: list[PlannedItem]


class PlanOut(BaseModel):
    days: list[PlannedDay]


def plan_trip(body: PlanIn) -> PlanOut:
    if settings.ai_mock:
        days = []
        for n in range(1, body.days + 1):
            city = body.city_ids[(n - 1) % len(body.city_ids)] if body.city_ids else 0
            places = [p for p in body.places if p.city_id == city][:3]
            offer = next((o for o in body.offers if o.city_id == city), None)
            items = [
                PlannedItem(place_id=p.place_id, start_time=f"{9 + 3 * i:02d}:00", cost=p.ticket_price or 0)
                for i, p in enumerate(places)
            ]
            days.append(
                PlannedDay(day_number=n, city_id=city, title=f"Day {n}", offer_id=offer and offer.offer_id, items=items)
            )
        return PlanOut(days=days)
    # TODO(Person 2): call the LLM agent here.
    raise NotImplementedError


@router.post("/plan", response_model=PlanOut, summary="Trip planner (AI)")
def plan_route(body: PlanIn) -> PlanOut:
    return plan_trip(body)
