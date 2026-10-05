"""Feature T5 · Chat that edits the trip. Owner: Person 3."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.chat.schemas import MessageIn

router = APIRouter(tags=["T5 · Chat"])
OWNER = "Person 3"
traveler = require_role("traveler")


@router.get("/trips/{trip_id}/messages")
def list_messages(trip_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: opening the chat should show the earlier conversation."""
    raise not_implemented(OWNER)


@router.post("/trips/{trip_id}/messages", status_code=201)
def send_message(trip_id: int, body: MessageIn, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """AI. Why: the traveler asks in plain words ("make day 2 lighter", "cheaper hotel in Luxor").
    Then: calls app/ai/chat_agent.py, saves the reply and a proposed change in trip_changes."""
    raise not_implemented(OWNER)


@router.post("/trip-changes/{change_id}/keep")
def keep_change(change_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: the traveler accepts the change.
    Then: applies the diff to trip_days / trip_items and calls trips/totals.recalculate_total()."""
    raise not_implemented(OWNER)


@router.post("/trip-changes/{change_id}/undo")
def undo_change(change_id: int, user: User = Depends(traveler), db: Session = Depends(get_db)):
    """Why: the traveler changed their mind.
    Then: restores the trip from the saved before-state in diff."""
    raise not_implemented(OWNER)
