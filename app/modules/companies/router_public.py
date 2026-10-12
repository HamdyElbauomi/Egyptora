"""Feature T9 · Company profile and reviews (traveler side)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.companies.schemas import CompanyPublicOut, ReviewIn
from app.modules.companies.service import get_company_or_404, to_public_out

router = APIRouter(prefix="/companies", tags=["T9 · Company reviews"])


@router.get("/{company_id}", response_model=CompanyPublicOut)
def company_profile(company_id: int, db: Session = Depends(get_db)) -> CompanyPublicOut:
    """Why: travelers decide which offer to trust partly by company reputation. Public, no login.
    Only approved companies are visible; pending, rejected or suspended ones return 404.
    Then: shown next to each offer in the hotel's offer list."""
    company = get_company_or_404(db, company_id)
    if company.status != "approved":
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Company {company_id} not found")
    return to_public_out(company)


@router.get("/{company_id}/reviews")
def company_reviews(company_id: int, db: Session = Depends(get_db)):
    """Why: travelers read what others said before choosing. (Built with the reviews feature.)"""
    raise not_implemented("Person 1")


@router.post("/{company_id}/reviews", status_code=201)
def add_review(
    company_id: int, body: ReviewIn, user: User = Depends(require_role("traveler")), db: Session = Depends(get_db)
):
    """Why: after the trip, the traveler rates the company. (Built with the reviews feature.)"""
    raise not_implemented("Person 1")
