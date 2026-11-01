"""The chat agent with a language model (USE_LLM=true). Same contract as the rules agent: ChatIn -> ChatOut.

The model does what it is good at: understanding the traveler (English or Egyptian Arabic) and writing the
reply. It answers with one small action ("set this hotel", "remove that place"); the code below turns the
action into the new state of each day it touches, computing times the same way the rules agent does.
Ids the model invents are refused, so a confused answer falls back to the rules agent instead of a bad change.
"""

import json

from app.ai.chat_agent import (
    DEFAULT_VISIT_MIN,
    GAP_MIN,
    ChatIn,
    ChatOut,
    ItemAfter,
    ProposedChange,
    day_after,
    hhmm,
    items_of,
    to_min,
)
from app.ai.llm import LLMError, complete_json

SYSTEM = """You are Egyptora's trip assistant. A traveler is changing their Egypt trip by chatting.

You get the trip (days, places, tonight's hotel offer per day), the places that could be added (with ids),
the live hotel offers in the trip's cities (with ids and prices) and the recent chat.

Choose at most ONE action:
- {"type": "set_hotel", "offer_id": <id from offers>, "day_numbers": [<days in that offer's city>]}
  for cheaper / better / different hotels. Cheaper = lower price_per_night; better = more stars, then trust.
- {"type": "remove_place", "place_id": <id of a place already in the trip>}
  also for "make day N lighter": remove that day's last or longest visit.
- {"type": "add_place", "place_id": <id from places>, "day_number": <a day in that place's city, or null>}
- {"type": "none"} when you only answer a question, need more detail, or nothing fits.

Only use ids that appear in the data. Never invent places, hotels or prices.
Write "reply" in the language of the traveler's LATEST message (English, or Egyptian Arabic if it is Arabic),
1-3 sentences,
saying what you changed and why. The traveler still has to tap Keep, so don't say it is done for sure.
"summary" is one short English line for the change card, like "Day 2: removed Khan el-Khalili".
"explanation" is one short English line on why it helps.

Reply with a JSON object only:
{"reply": "...", "action": {...}, "summary": "...", "explanation": "..."}"""


def context(body: ChatIn) -> str:
    days = [
        {
            "day_number": d["day_number"],
            "city_id": d["city_id"],
            "city": d["city_name"],
            "hotel": d["hotel"] and {k: d["hotel"][k] for k in ("offer_id", "hotel_name", "stars", "price_per_night")},
            "items": [
                {
                    "place_id": i["place_id"],
                    "name": i["place_name"] or i["note"],
                    "type": i["type"],
                    "start": i["start_time"],
                }
                for i in d["items"]
            ],
        }
        for d in body.trip["itinerary"]
    ]
    data = {
        "trip": {"title": body.trip.get("title"), "total_cost": body.trip.get("total_cost"), "days": days},
        "places_you_can_add": [p.model_dump() for p in body.places][:80],
        "hotel_offers": [o.model_dump() for o in body.offers][:60],
        "recent_chat": body.history[-6:],
        "message": body.message,
    }
    return json.dumps(data, ensure_ascii=False, default=str)


def llm_agent(body: ChatIn) -> ChatOut:
    out = complete_json(SYSTEM, context(body), max_tokens=500)
    reply = out.get("reply")
    action = out.get("action") or {"type": "none"}
    if not isinstance(reply, str) or not reply.strip() or not isinstance(action, dict):
        raise LLMError("the reply is missing")
    kind = action.get("type")
    if kind in (None, "none"):
        return ChatOut(reply=reply.strip())
    days = run_action(body, kind, action)
    summary = str(out.get("summary") or "").strip() or "Suggested change"
    explanation = str(out.get("explanation") or "").strip() or "As you asked."
    return ChatOut(reply=reply.strip(), change=ProposedChange(summary=summary, explanation=explanation, days=days))


def as_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise LLMError(f"not an id: {value!r}") from exc


def run_action(body: ChatIn, kind: str, action: dict):
    trip_days = body.trip["itinerary"]
    by_number = {d["day_number"]: d for d in trip_days}

    if kind == "set_hotel":
        offer = next((o for o in body.offers if o.offer_id == as_int(action.get("offer_id"))), None)
        if offer is None:
            raise LLMError("unknown offer")
        city_days = [d for d in trip_days if d["city_id"] == offer.city_id]
        wanted = [as_int(n) for n in action.get("day_numbers") or []]
        chosen = [d for d in city_days if d["day_number"] in wanted] or city_days
        if not chosen:
            raise LLMError("that hotel is in a city the trip doesn't visit")
        return [day_after(d, offer_id=offer.offer_id) for d in chosen]

    if kind == "remove_place":
        place_id = as_int(action.get("place_id"))
        day = next((d for d in trip_days if any(i["place_id"] == place_id for i in d["items"])), None)
        if day is None:
            raise LLMError("that place isn't in the trip")
        return [day_after(day, items=[i for i in items_of(day) if i.place_id != place_id])]

    if kind == "add_place":
        place = next((p for p in body.places if p.place_id == as_int(action.get("place_id"))), None)
        in_trip = {i["place_id"] for d in trip_days for i in d["items"]}
        if place is None or place.place_id in in_trip:
            raise LLMError("unknown place, or already in the trip")
        city_days = [d for d in trip_days if d["city_id"] == place.city_id]
        if not city_days:
            raise LLMError("that place is in a city the trip doesn't visit")
        asked = by_number.get(as_int(action["day_number"])) if action.get("day_number") is not None else None
        day = asked if asked in city_days else min(city_days, key=lambda d: (len(d["items"]), d["day_number"]))
        ends = [to_min(i["end_time"] or i["start_time"]) for i in day["items"] if i["start_time"]]
        start = max(ends) + GAP_MIN if ends else 9 * 60
        new = ItemAfter(
            place_id=place.place_id,
            start_time=hhmm(start),
            end_time=hhmm(start + (place.visit_minutes or DEFAULT_VISIT_MIN)),
            cost=place.ticket_price or 0,
        )
        return [day_after(day, items=items_of(day) + [new])]

    raise LLMError(f"unknown action {kind!r}")
