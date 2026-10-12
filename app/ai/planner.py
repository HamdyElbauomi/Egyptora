"""AI piece: trip planner agent. Owner: Person 2.

Why: decides which places go on which day, in what order, and which hotel offer fits the budget.
Then: POST /trips/generate saves the returned plan into trip_days and trip_items.

AI_MOCK=true uses plan_with_rules() below: a simple, predictable planner the app can rely on
until the LLM agent is ready. The real agent must return the same PlanOut shape.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

DAY_START_MIN = 9 * 60  # 09:00
DAY_END_MIN = 18 * 60  # last visit ends by 18:00
DEFAULT_VISIT_MIN = 90
GAP_MIN = 30  # moving between places


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
    offers: list[CandidateOffer]  # per city, already ordered by how well they fit budget_level
    variant: int = 0  # 0 = first plan; regenerate sends another number to get a different version


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


def hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def split_days(days: int, city_ids: list[int]) -> list[int]:
    """Gives each city a block of consecutive days, in the order given. Extra days go to the first cities.
    7 days over [Cairo, Luxor, Aswan] -> Cairo x3, Luxor x2, Aswan x2."""
    if not city_ids:
        return []
    base, extra = divmod(days, len(city_ids))
    result: list[int] = []
    for i, city_id in enumerate(city_ids):
        result += [city_id] * (base + (1 if i < extra else 0))
    return result


def fill_day(queue: list[CandidatePlace]) -> list[PlannedItem]:
    """Takes places from the front of the queue while they fit between 09:00 and 18:00."""
    items: list[PlannedItem] = []
    clock = DAY_START_MIN
    while queue:
        place = queue[0]
        length = place.visit_minutes or DEFAULT_VISIT_MIN
        if items and clock + length > DAY_END_MIN:
            break
        queue.pop(0)
        items.append(
            PlannedItem(
                place_id=place.place_id,
                start_time=hhmm(clock),
                end_time=hhmm(min(clock + length, 23 * 60 + 59)),
                cost=place.ticket_price or 0,
            )
        )
        clock += length + GAP_MIN
    return items


def pick_offer(offers: list[CandidateOffer], nightly_allowance: float | None, variant: int) -> CandidateOffer | None:
    """The first offer that fits the money left per night; the cheapest when none fits."""
    if not offers:
        return None
    ordered = offers[variant % len(offers) :] + offers[: variant % len(offers)]
    if nightly_allowance is None:
        return ordered[0]
    fitting = [o for o in ordered if o.price_per_night <= nightly_allowance]
    return fitting[0] if fitting else min(offers, key=lambda o: o.price_per_night)


def plan_with_rules(body: PlanIn) -> PlanOut:
    wanted = set(body.interest_ids)
    day_cities = split_days(body.days, body.city_ids)

    # Places per city: most matching interests first. A variant rotates the list for a different plan.
    queues: dict[int, list[CandidatePlace]] = {}
    for city_id in body.city_ids:
        places = sorted(
            (p for p in body.places if p.city_id == city_id),
            key=lambda p: (-len(wanted & set(p.interest_ids)), p.place_id),
        )
        if body.variant and places:
            shift = body.variant % len(places)
            places = places[shift:] + places[:shift]
        queues[city_id] = places

    # Spread a city's places over its days: each day takes its fair share, then fills by time.
    days: list[PlannedDay] = []
    for index, city_id in enumerate(day_cities):
        days_left_here = day_cities[index:].count(city_id)
        queue = queues[city_id]
        share = -(-len(queue) // days_left_here) if queue else 0  # ceil
        today = queue[:share]
        items = fill_day(today)
        queues[city_id] = today + queue[share:]  # places that didn't fit go back to the front
        if not items:
            items = [PlannedItem(place_id=None, type="free_time", start_time="10:00", note="Free time to explore")]
        days.append(PlannedDay(day_number=index + 1, city_id=city_id, title="", offer_id=None, items=items))

    # Hotels: keep the same hotel for the whole stay in a city.
    tickets = sum(i.cost for d in days for i in d.items)
    allowance = (body.budget_total - tickets) / body.days if body.budget_total else None
    for city_id in body.city_ids:
        offer = pick_offer([o for o in body.offers if o.city_id == city_id], allowance, body.variant)
        for day in days:
            if day.city_id == city_id:
                day.offer_id = offer.offer_id if offer else None
    return PlanOut(days=days)


def plan_trip(body: PlanIn) -> PlanOut:
    if settings.ai_mock:
        return plan_with_rules(body)
    # TODO(Person 2): call the LLM agent here. It gets the same candidates and must return PlanOut.
    raise NotImplementedError


@router.post("/plan", response_model=PlanOut, summary="Trip planner (AI)")
def plan_route(body: PlanIn) -> PlanOut:
    return plan_trip(body)
