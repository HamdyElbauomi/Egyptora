"""Chat logic: build the agent's input, check and price its proposed change, Keep and Undo. Owner: Person 3.

A change is stored in trip_changes.diff as:
    {"day_ids": [...], "day_numbers": [...], "before": {day_id: DAY}, "after": {day_id: DAY}}
    DAY = {"offer_id": int | None, "items": [{"place_id", "type", "start_time", "end_time", "note", "cost"}]}
before is read from the database (never from the AI); after is the AI's proposal after our checks.
Keep writes "after" only if the days still look like "before"; Undo writes "before" back only if
the days still look like "after". So a stale suggestion can never overwrite newer edits.
"""

from datetime import time

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.chat_agent import ChatIn, ChatOffer, ChatOut, ChatPlace, ProposedChange
from app.modules.accounts.models import User
from app.modules.chat.models import ChatMessage, TripChange
from app.modules.chat.schemas import ChangeOut, MessageOut
from app.modules.companies.models import Company
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer
from app.modules.offers.service import live_conditions
from app.modules.places.models import Place
from app.modules.trips.models import ITEM_TYPES, Trip, TripDay, TripItem
from app.modules.trips.service import trip_city_ids

HISTORY_LIMIT = 10


class InvalidChange(Exception):
    """The agent proposed something we can't apply (unknown place, wrong city, dead offer...)."""


def get_own_change(db: Session, user: User, change_id: int) -> tuple[TripChange, Trip]:
    row = db.execute(
        select(TripChange, Trip)
        .join(Trip, Trip.id == TripChange.trip_id)
        .where(TripChange.id == change_id, Trip.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Change not found")
    return row[0], row[1]


# ---------- what the agent gets ----------


def agent_places(db: Session, city_ids: list[int]) -> list[ChatPlace]:
    places = db.scalars(select(Place).where(Place.city_id.in_(city_ids)).order_by(Place.id))
    return [
        ChatPlace(
            place_id=p.id, city_id=p.city_id, name=p.name, visit_minutes=p.visit_minutes, ticket_price=p.ticket_price
        )
        for p in places
    ]


def agent_offers(db: Session, city_ids: list[int]) -> list[ChatOffer]:
    rows = db.execute(
        select(Offer, Company, Hotel)
        .join(Company, Company.id == Offer.company_id)
        .join(Hotel, Hotel.id == Offer.hotel_id)
        .where(Hotel.city_id.in_(city_ids), live_conditions())
        .order_by(Offer.price_per_night, Offer.id)
    ).all()
    return [
        ChatOffer(
            offer_id=o.id,
            city_id=h.city_id,
            hotel_name=h.name,
            stars=h.stars,
            company_name=c.name,
            price_per_night=o.price_per_night,
            trust_score=float(c.trust_score) if c.trust_score is not None else None,
        )
        for o, c, h in rows
    ]


def history(db: Session, trip_id: int) -> list[dict]:
    rows = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.trip_id == trip_id)
            .order_by(ChatMessage.id.desc())
            .limit(HISTORY_LIMIT)
        )
    )
    return [{"role": m.role, "content": m.content} for m in reversed(rows)]


def build_agent_input(db: Session, trip_json: dict, trip_id: int, message: str) -> ChatIn:
    city_ids = trip_city_ids(db, trip_id) or [d["city_id"] for d in trip_json["itinerary"]]
    return ChatIn(
        message=message,
        trip=trip_json,
        history=history(db, trip_id),
        places=agent_places(db, city_ids),
        offers=agent_offers(db, city_ids),
    )


# ---------- snapshots ----------


def norm_time(value) -> str | None:
    if value is None or value == "":
        return None
    t = value if isinstance(value, time) else time.fromisoformat(value)
    return t.replace(second=0, microsecond=0).isoformat()


def snapshot(db: Session, day_ids: list[int]) -> dict:
    """The current state of these days, in the diff format. A deleted day shows as None."""
    days = {d.id: d for d in db.scalars(select(TripDay).where(TripDay.id.in_(day_ids)))}
    items: dict[int, list[dict]] = {d: [] for d in day_ids}
    for i in db.scalars(
        select(TripItem).where(TripItem.trip_day_id.in_(day_ids)).order_by(TripItem.position, TripItem.id)
    ):
        items[i.trip_day_id].append(
            {
                "place_id": i.place_id,
                "type": i.type,
                "start_time": norm_time(i.start_time),
                "end_time": norm_time(i.end_time),
                "note": i.note,
                "cost": i.cost,
            }
        )
    return {str(d): ({"offer_id": days[d].offer_id, "items": items[d]} if d in days else None) for d in day_ids}


def write_days(db: Session, state: dict) -> None:
    """Replaces each day's hotel and items with the given state."""
    for day_id, day_state in state.items():
        day = db.get(TripDay, int(day_id))
        day.offer_id = day_state["offer_id"]
        db.execute(delete(TripItem).where(TripItem.trip_day_id == day.id))
        for n, item in enumerate(day_state["items"]):
            db.add(
                TripItem(
                    trip_day_id=day.id,
                    place_id=item["place_id"],
                    type=item["type"],
                    start_time=time.fromisoformat(item["start_time"]) if item["start_time"] else None,
                    end_time=time.fromisoformat(item["end_time"]) if item["end_time"] else None,
                    note=item["note"],
                    cost=item["cost"],
                    position=n,
                )
            )
    db.flush()


def state_cost(db: Session, state: dict) -> int:
    offer_ids = {d["offer_id"] for d in state.values() if d and d["offer_id"]}
    prices = dict(db.execute(select(Offer.id, Offer.price_per_night).where(Offer.id.in_(offer_ids))).all())
    return sum(
        sum(i["cost"] for i in d["items"]) + prices.get(d["offer_id"], 0) for d in state.values() if d is not None
    )


# ---------- checking the agent's proposal ----------


def check_proposal(db: Session, trip: Trip, change: ProposedChange) -> dict:
    """Turns the agent's days into the "after" state, or raises InvalidChange."""
    days = {d.id: d for d in db.scalars(select(TripDay).where(TripDay.trip_id == trip.id))}
    after: dict[str, dict] = {}
    for proposed in change.days:
        day = days.get(proposed.day_id)
        if day is None:
            raise InvalidChange(f"day {proposed.day_id} is not in this trip")
        if str(day.id) in after:
            raise InvalidChange(f"day {day.id} is listed twice")
        if proposed.offer_id is not None:
            ok = db.execute(
                select(Offer.id)
                .join(Company, Company.id == Offer.company_id)
                .join(Hotel, Hotel.id == Offer.hotel_id)
                .where(Offer.id == proposed.offer_id, Hotel.city_id == day.city_id, live_conditions())
            ).first()
            if not ok:
                raise InvalidChange(f"offer {proposed.offer_id} is not live in the day's city")
        items = []
        for item in proposed.items:
            if item.type not in ITEM_TYPES:
                raise InvalidChange(f"unknown item type {item.type}")
            if item.type == "visit" and item.place_id is None:
                raise InvalidChange("a visit needs a place")
            if item.place_id is not None:
                city = db.scalar(select(Place.city_id).where(Place.id == item.place_id))
                if city != day.city_id:
                    raise InvalidChange(f"place {item.place_id} is not in the day's city")
            if item.cost < 0:
                raise InvalidChange("negative cost")
            try:
                start, end = norm_time(item.start_time), norm_time(item.end_time)
            except ValueError as exc:
                raise InvalidChange("bad time") from exc
            items.append(
                {
                    "place_id": item.place_id,
                    "type": item.type,
                    "start_time": start,
                    "end_time": end,
                    "note": item.note,
                    "cost": item.cost,
                }
            )
        after[str(day.id)] = {"offer_id": proposed.offer_id, "items": items}

    # No place twice in the whole trip, counting the days the change doesn't touch.
    untouched = [d for d in days if str(d) not in after]
    places = [i["place_id"] for d in after.values() for i in d["items"] if i["place_id"]]
    places += [
        p for p in db.scalars(select(TripItem.place_id).where(TripItem.trip_day_id.in_(untouched))) if p is not None
    ]
    if len(places) != len(set(places)):
        raise InvalidChange("a place would be in the trip twice")
    return after


def propose(db: Session, trip: Trip, reply_message: ChatMessage, out: ChatOut) -> TripChange | None:
    """Saves the agent's change as "proposed", or returns None when there is nothing valid to propose."""
    if out.change is None or not out.change.days:
        return None
    try:
        after = check_proposal(db, trip, out.change)
    except InvalidChange as exc:
        reply_message.content += f" (I couldn't prepare that change safely: {exc}.)"
        return None
    day_ids = [int(d) for d in after]
    before = snapshot(db, day_ids)
    if before == after:
        return None
    numbers = dict(db.execute(select(TripDay.id, TripDay.day_number).where(TripDay.id.in_(day_ids))).all())
    change = TripChange(
        trip_id=trip.id,
        message_id=reply_message.id,
        summary=out.change.summary,
        explanation=out.change.explanation,
        cost_delta=state_cost(db, after) - state_cost(db, before),
        diff={
            "day_ids": day_ids,
            "day_numbers": sorted(numbers[d] for d in day_ids),
            "before": before,
            "after": after,
        },
    )
    db.add(change)
    db.flush()
    return change


# ---------- Keep and Undo ----------


def keep(db: Session, change: TripChange) -> None:
    if change.status != "proposed":
        raise HTTPException(status.HTTP_409_CONFLICT, f"This change is already {change.status}")
    if snapshot(db, change.diff["day_ids"]) != change.diff["before"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "The trip changed since this suggestion. Ask the chat again.")
    write_days(db, change.diff["after"])
    change.status = "kept"


def undo(db: Session, change: TripChange) -> None:
    """A proposed change is just dismissed. A kept change is reversed."""
    if change.status == "undone":
        raise HTTPException(status.HTTP_409_CONFLICT, "This change is already undone")
    if change.status == "kept":
        if snapshot(db, change.diff["day_ids"]) != change.diff["after"]:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Those days were edited after this change, so it can't be undone safely"
            )
        write_days(db, change.diff["before"])
    change.status = "undone"


# ---------- output ----------


def to_change_out(change: TripChange) -> ChangeOut:
    return ChangeOut(
        id=change.id,
        summary=change.summary,
        explanation=change.explanation,
        cost_delta=change.cost_delta,
        status=change.status,
        day_numbers=change.diff.get("day_numbers", []),
        created_at=change.created_at,
    )


def to_message_out(message: ChatMessage, change: TripChange | None = None) -> MessageOut:
    return MessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        change=to_change_out(change) if change else None,
        created_at=message.created_at,
    )
