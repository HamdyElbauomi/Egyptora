"""AI piece: chat agent that edits the trip. Owner: Person 3.

Why: reads the trip and the traveler's message, returns a reply and at most one proposed change.
Then: the backend checks the change, computes its cost, saves it in trip_changes and waits for Keep or Undo.

The contract (the real LLM agent must keep it):
- In: the message, the full trip (same shape as GET /trips/{id}), the last messages,
  the places it may use (trip cities only) and the live hotel offers in those cities.
- Out: a reply, and optionally a change = the NEW full state of each day it touches
  (that day's hotel offer_id and its full item list in order). Days it doesn't list stay as they are.
  The backend works out the before-state and the cost difference itself.

AI_MOCK=true uses rules_agent() below. It understands a few requests in English and Egyptian Arabic:
cheaper / better hotel, make a day lighter, add a place, remove a place.
"""

import re

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI (internal)"])

GAP_MIN = 30
DEFAULT_VISIT_MIN = 90


class ChatPlace(BaseModel):
    place_id: int
    city_id: int
    name: str
    visit_minutes: int | None = None
    ticket_price: int | None = None


class ChatOffer(BaseModel):
    offer_id: int
    city_id: int
    hotel_name: str
    stars: int | None = None
    company_name: str
    price_per_night: int
    trust_score: float | None = None


class ChatIn(BaseModel):
    message: str
    trip: dict  # the full trip as returned by GET /trips/{id}
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}], oldest first
    places: list[ChatPlace] = []
    offers: list[ChatOffer] = []


class ItemAfter(BaseModel):
    place_id: int | None = None
    type: str = "visit"
    start_time: str | None = None  # "09:00" or "09:00:00"
    end_time: str | None = None
    note: str | None = None
    cost: int = 0


class DayAfter(BaseModel):
    day_id: int
    offer_id: int | None
    items: list[ItemAfter]


class ProposedChange(BaseModel):
    summary: str  # one line for the change card, e.g. "Day 2: removed Khan el-Khalili"
    explanation: str  # why this helps
    days: list[DayAfter]


class ChatOut(BaseModel):
    reply: str
    change: ProposedChange | None = None


# ---------- rules agent (AI_MOCK) ----------

WORDS = {
    "hotel": ("hotel", "stay", "فندق", "اوتيل", "أوتيل"),
    "cheaper": ("cheap", "cheaper", "budget", "save", "أرخص", "ارخص", "رخيص", "وفر"),
    "better": ("better", "nicer", "luxury", "upgrade", "more stars", "أحسن", "احسن", "أفضل", "افضل", "فخم"),
    "lighter": ("lighter", "less", "relax", "tired", "rest", "أخف", "اخف", "خفف", "ريح", "راحة"),
    "add": ("add", "include", "visit", "ضيف", "أضف", "اضف", "زود", "عايز اروح", "عايز أروح"),
    "remove": ("remove", "delete", "skip", "drop", "شيل", "احذف", "الغي", "ألغي", "مش عايز"),
}
CITY_ALIASES = {
    "cairo": ("القاهرة", "القاهره"),
    "giza": ("الجيزة", "الجيزه"),
    "luxor": ("الأقصر", "الاقصر"),
    "aswan": ("أسوان", "اسوان"),
    "alexandria": ("الإسكندرية", "الاسكندرية", "اسكندرية", "إسكندرية"),
    "hurghada": ("الغردقة", "الغردقه"),
    "sharm el-sheikh": ("شرم",),
}
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def has(text: str, key: str) -> bool:
    return any(w in text for w in WORDS[key])


def to_min(value: str | None) -> int | None:
    if not value:
        return None
    h, m = value.split(":")[:2]
    return int(h) * 60 + int(m)


def hhmm(minutes: int) -> str:
    minutes = max(0, min(minutes, 23 * 60 + 59))
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def items_of(day: dict) -> list[ItemAfter]:
    return [
        ItemAfter(
            place_id=i["place_id"],
            type=i["type"],
            start_time=i["start_time"],
            end_time=i["end_time"],
            note=i["note"],
            cost=i["cost"],
        )
        for i in day["items"]
    ]


def day_after(day: dict, *, offer_id: int | None = ..., items: list[ItemAfter] | None = None) -> DayAfter:
    return DayAfter(
        day_id=day["id"],
        offer_id=(day["hotel"] or {}).get("offer_id") if offer_id is ... else offer_id,
        items=items if items is not None else items_of(day),
    )


def mentioned_day(text: str, days: list[dict]) -> dict | None:
    match = re.search(r"(?:day|يوم|اليوم)\s*(\d+)", text.translate(ARABIC_DIGITS))
    if match:
        n = int(match.group(1))
        return next((d for d in days if d["day_number"] == n), None)
    return None


def mentioned_city(text: str, trip: dict) -> int | None:
    for city in trip["cities"]:
        name = city["name"].lower()
        if name in text or any(alias in text for alias in CITY_ALIASES.get(name, ())):
            return city["id"]
    return None


GENERIC_WORDS = {"temple", "complex", "museum", "mosque", "church", "market", "street", "the", "great"}


def match_score(text: str, name: str, ignore: set[str]) -> int:
    """2 = the full name is in the message, 1 = all its distinctive words are, 0 = no match.
    City names and generic words ("temple", "museum") don't count as distinctive."""
    name = name.lower()
    if name in text:
        return 2
    words = [w for w in re.findall(r"[\w-]+", name) if len(w) >= 4 and w not in GENERIC_WORDS and w not in ignore]
    return 1 if words and all(w in text for w in words) else 0


def best_match(text: str, trip: dict, named: list[tuple[str, object]]):
    """The candidate whose name matches the message best (full name first, then the longest name)."""
    ignore = {w for c in trip["cities"] for w in c["name"].lower().split()}
    scored = [(match_score(text, name, ignore), len(name), obj) for name, obj in named]
    scored = [s for s in scored if s[0] > 0]
    return max(scored, key=lambda s: (s[0], s[1]))[2] if scored else None


def change_hotel(text: str, trip: dict, offers: list[ChatOffer]) -> ChatOut:
    days = trip["itinerary"]
    day = mentioned_day(text, days)
    city_id = day["city_id"] if day else mentioned_city(text, trip)
    city_ids = [city_id] if city_id else [c["id"] for c in trip["cities"]]
    better = has(text, "better") and not has(text, "cheaper")

    changed: list[DayAfter] = []
    picks: list[str] = []
    for cid in city_ids:
        options = [o for o in offers if o.city_id == cid]
        if not options:
            continue
        if better:
            pick = max(options, key=lambda o: (o.stars or 0, o.trust_score or 0, -o.price_per_night))
        else:
            pick = min(options, key=lambda o: (o.price_per_night, -(o.trust_score or 0)))
        city_days = [d for d in days if d["city_id"] == cid]
        if all((d["hotel"] or {}).get("offer_id") == pick.offer_id for d in city_days):
            continue
        changed += [day_after(d, offer_id=pick.offer_id) for d in city_days]
        picks.append(f"{pick.hotel_name} with {pick.company_name} ({pick.price_per_night} EGP/night)")

    word = "better" if better else "cheaper"
    if not changed:
        return ChatOut(reply=f"You already have the {'best' if better else 'cheapest'} hotel I can find there.")
    return ChatOut(
        reply=f"Here is a {word} option: {', '.join(picks)}. Tap Keep to switch.",
        change=ProposedChange(
            summary=f"Switch to {', '.join(picks)}",
            explanation="Highest stars, then the most trusted company."
            if better
            else "The lowest live price in that city; the same hotel for the whole stay.",
            days=changed,
        ),
    )


def make_lighter(text: str, trip: dict) -> ChatOut:
    days = trip["itinerary"]
    day = mentioned_day(text, days) or max(days, key=lambda d: (len(d["items"]), -d["day_number"]), default=None)
    visits = [i for i in (day["items"] if day else []) if i["type"] == "visit"]
    if not day or len(visits) <= 1:
        return ChatOut(reply="That day is already light, there is only one visit or less.")
    dropped = visits[-1]
    items = [i for i in items_of(day) if not (i.place_id == dropped["place_id"] and i.type == "visit")]
    return ChatOut(
        reply=f"I removed {dropped['place_name']} from day {day['day_number']} so the afternoon is free.",
        change=ProposedChange(
            summary=f"Day {day['day_number']}: removed {dropped['place_name']}",
            explanation="The last visit of the day goes; the morning stays the same.",
            days=[day_after(day, items=items)],
        ),
    )


def add_place(text: str, trip: dict, places: list[ChatPlace]) -> ChatOut | None:
    in_trip = {i["place_id"] for d in trip["itinerary"] for i in d["items"]}
    place = best_match(text, trip, [(p.name, p) for p in places if p.place_id not in in_trip])
    if place is None:
        return None
    city_days = [d for d in trip["itinerary"] if d["city_id"] == place.city_id]
    if not city_days:
        return ChatOut(reply=f"{place.name} is in a city that isn't in this trip.")
    asked = mentioned_day(text, trip["itinerary"])
    day = asked if asked in city_days else min(city_days, key=lambda d: (len(d["items"]), d["day_number"]))
    ends = [to_min(i["end_time"] or i["start_time"]) for i in day["items"] if i["start_time"]]
    start = max(ends) + GAP_MIN if ends else 9 * 60
    length = place.visit_minutes or DEFAULT_VISIT_MIN
    new = ItemAfter(
        place_id=place.place_id, start_time=hhmm(start), end_time=hhmm(start + length), cost=place.ticket_price or 0
    )
    return ChatOut(
        reply=f"I added {place.name} to day {day['day_number']} at {hhmm(start)}.",
        change=ProposedChange(
            summary=f"Day {day['day_number']}: added {place.name}",
            explanation="It goes on the lightest day in that city, after the last visit.",
            days=[day_after(day, items=items_of(day) + [new])],
        ),
    )


def remove_place(text: str, trip: dict) -> ChatOut | None:
    found = best_match(
        text, trip, [(i["place_name"], (d, i)) for d in trip["itinerary"] for i in d["items"] if i["place_name"]]
    )
    if found is None:
        return None
    day, item = found
    items = [i for i in items_of(day) if i.place_id != item["place_id"]]
    return ChatOut(
        reply=f"I removed {item['place_name']} from day {day['day_number']}.",
        change=ProposedChange(
            summary=f"Day {day['day_number']}: removed {item['place_name']}",
            explanation="Removed as you asked; the rest of the day stays the same.",
            days=[day_after(day, items=items)],
        ),
    )


HELP = (
    "I can change your trip for you. Try: “cheaper hotel in Luxor”, “better hotel”, "
    "“make day 2 lighter”, “add Luxor Museum”, or “remove Khan el-Khalili”."
)


def rules_agent(body: ChatIn) -> ChatOut:
    text = body.message.lower()
    trip = body.trip
    if not trip.get("itinerary"):
        return ChatOut(reply="This trip has no days yet. Try regenerating it first.")
    if has(text, "hotel") or (has(text, "cheaper") and not has(text, "remove")):
        return change_hotel(text, trip, body.offers)
    if has(text, "remove"):
        return remove_place(text, trip) or ChatOut(reply="I couldn't find that place in your trip.")
    if has(text, "add"):
        return add_place(text, trip, body.places) or ChatOut(
            reply="I couldn't find that place in your trip's cities, or it's already in the trip."
        )
    if has(text, "lighter"):
        return make_lighter(text, trip)
    return ChatOut(reply=HELP)


def chat(body: ChatIn) -> ChatOut:
    if settings.ai_mock:
        return rules_agent(body)
    # TODO(Person 3): call the LLM agent here with the same ChatIn, and parse its answer into ChatOut.
    raise NotImplementedError


@router.post("/chat", response_model=ChatOut, summary="Chat agent (AI)")
def chat_route(body: ChatIn) -> ChatOut:
    return chat(body)
