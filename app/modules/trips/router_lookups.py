"""Feature T2 · Preferences lookups. Owner: Person 2 (reads Person 3's cities and interests tables)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented

router = APIRouter(tags=["T2 · Preferences"])
OWNER = "Person 2"


@router.get("/interests")
def list_interests(db: Session = Depends(get_db)):
    """Why: preference step 1 needs the list of interest chips.
    Then: the chosen interest ids go into POST /trips/generate."""
    raise not_implemented(OWNER)


@router.get("/cities")
def list_cities(db: Session = Depends(get_db)):
    """Why: preference step 4 needs the destination cards.
    Then: the chosen city ids go into POST /trips/generate."""
    raise not_implemented(OWNER)


@router.get("/cities/suggest")
def suggest_cities(
    interests: list[int] = Query(default=[]),
    days: int = 3,
    budget: str = "mid",
    db: Session = Depends(get_db),
):
    """Why: some travelers don't know where to go and tap "suggest for me".
    Then: returns cities to pre-select before POST /trips/generate."""
    raise not_implemented(OWNER)
