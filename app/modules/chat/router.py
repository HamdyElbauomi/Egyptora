"""Feature T5 · Chat that edits the trip. Owner: Person 3.

Flow: the traveler sends a message -> the agent replies and may propose ONE change -> the change card shows
the summary and the cost difference -> Keep applies it, Undo dismisses it (or reverses it after Keep).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chat_agent import chat
from app.core.database import get_db
from app.core.deps import require_role
from app.modules.accounts.models import User
from app.modules.chat import service
from app.modules.chat.models import ChatMessage, TripChange
from app.modules.chat.schemas import ChangeResultOut, ChatReplyOut, MessageIn, MessageOut
from app.modules.trips.service import get_own_trip, to_trip_out, touch
from app.modules.trips.totals import recalculate_total

router = APIRouter(tags=["T5 · Chat"])
traveler = require_role("traveler")


@router.get("/trips/{trip_id}/messages", response_model=list[MessageOut])
def list_messages(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> list[MessageOut]:
    """Why: opening the chat should show the earlier conversation, oldest first.
    Assistant messages carry their change card with its current status (proposed, kept or undone)."""
    trip = get_own_trip(db, user, trip_id)
    messages = list(db.scalars(select(ChatMessage).where(ChatMessage.trip_id == trip.id).order_by(ChatMessage.id)))
    changes = {c.message_id: c for c in db.scalars(select(TripChange).where(TripChange.trip_id == trip.id))}
    return [service.to_message_out(m, changes.get(m.id)) for m in messages]


@router.post("/trips/{trip_id}/messages", status_code=201, response_model=ChatReplyOut)
def send_message(
    trip_id: int, body: MessageIn, user: User = Depends(traveler), db: Session = Depends(get_db)
) -> ChatReplyOut:
    """AI. Why: the traveler asks in plain words ("make day 2 lighter", "cheaper hotel in Luxor", "add Luxor Museum").
    How: the agent (app/ai/chat_agent.py) gets the trip, the last messages, the places in the trip's cities and
    the live hotel offers there. It replies, and may propose one change. We check the change (places in the
    right city, live offers, no place twice) and work out cost_delta ourselves.
    Nothing changes yet. Then: POST /trip-changes/{id}/keep or /undo."""
    trip = get_own_trip(db, user, trip_id)
    agent_in = service.build_agent_input(db, to_trip_out(db, trip).model_dump(mode="json"), trip.id, body.content)

    question = ChatMessage(trip_id=trip.id, role="user", content=body.content)
    db.add(question)
    out = chat(agent_in)
    answer = ChatMessage(trip_id=trip.id, role="assistant", content=out.reply)
    db.add(answer)
    db.flush()
    change = service.propose(db, trip, answer, out)
    db.commit()
    return ChatReplyOut(message=service.to_message_out(question), reply=service.to_message_out(answer, change))


@router.post("/trip-changes/{change_id}/keep", response_model=ChangeResultOut)
def keep_change(change_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> ChangeResultOut:
    """Why: the traveler accepts the change.
    Applies it only if those days are still as they were when it was proposed (else 409: ask again).
    Returns the change and the updated trip with its new total."""
    change, trip = service.get_own_change(db, user, change_id)
    service.keep(db, change)
    recalculate_total(db, trip.id)
    touch(trip)
    db.commit()
    return ChangeResultOut(change=service.to_change_out(change), trip=to_trip_out(db, trip))


@router.post("/trip-changes/{change_id}/undo", response_model=ChangeResultOut)
def undo_change(change_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)) -> ChangeResultOut:
    """Why: the traveler doesn't want the change, or changed their mind after Keep.
    A proposed change is just dismissed. A kept change is reversed exactly, as long as those days
    weren't edited again after it (else 409)."""
    change, trip = service.get_own_change(db, user, change_id)
    service.undo(db, change)
    recalculate_total(db, trip.id)
    touch(trip)
    db.commit()
    return ChangeResultOut(change=service.to_change_out(change), trip=to_trip_out(db, trip))
