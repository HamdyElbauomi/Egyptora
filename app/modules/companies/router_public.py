"""Feature T9 · Company reviews and trust (traveler side). Owner: Person 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.companies.schemas import ReviewIn

router = APIRouter(prefix="/companies", tags=["T9 · Company reviews"])
OWNER = "Person 1"


@router.get("/{company_id}")
def company_profile(company_id: int, db: Session = Depends(get_db)):
    """Why: travelers decide which offer to trust partly by company reputation.
    Then: shown inside the offer list (Person 6)."""
    raise not_implemented(OWNER)


@router.get("/{company_id}/reviews")
def company_reviews(company_id: int, db: Session = Depends(get_db)):
    """Why: travelers read what others said before choosing."""
    raise not_implemented(OWNER)


@router.post("/{company_id}/reviews", status_code=201)
def add_review(
    company_id: int, body: ReviewIn, user: User = Depends(require_role("traveler")), db: Session = Depends(get_db)
):
    """Why: after the trip, the traveler rates the company.
    Then: runs app/ai/sentiment.py and recomputes trust_score (trust.py),
    which changes Best value ranking (Person 6)."""
    raise not_implemented(OWNER)
