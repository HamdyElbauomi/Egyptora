"""Feature A2 · Companies, verification and trust (admin). Owner: Person 1."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.companies.schemas import AnalyzeReviewsIn, ApproveChecklistIn, RejectIn

router = APIRouter(prefix="/admin/companies", tags=["A2 · Admin companies"])
OWNER = "Person 1"
admin = require_role("admin")


@router.get("")
def list_companies(status: str | None = None, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin needs a queue of companies waiting for approval (pending first).
    Then: opens one company in GET /admin/companies/{id}."""
    raise not_implemented(OWNER)


@router.get("/{company_id}")
def company_detail(company_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin checks the license, social pages and offers before deciding.
    Then: approve, reject or suspend."""
    raise not_implemented(OWNER)


@router.post("/{company_id}/approve")
def approve(company_id: int, body: ApproveChecklistIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the checklist gives a starting trust score before any traveler reviews exist (trust.py).
    Then: the company can publish offers (Person 6) and its trust score shows next to them."""
    raise not_implemented(OWNER)


@router.post("/{company_id}/reject")
def reject(company_id: int, body: RejectIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: unlicensed or fake companies must be kept out.
    Then: the company sees the reason in GET /company/me."""
    raise not_implemented(OWNER)


@router.post("/{company_id}/suspend")
def suspend(company_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: a company that cheats travelers must be stopped fast.
    Then: all its offers pause (call Person 6's app/modules/offers/service.py: pause_all_for_company)."""
    raise not_implemented(OWNER)


@router.post("/{company_id}/analyze-reviews")
def analyze_reviews(
    company_id: int, body: AnalyzeReviewsIn, user: User = Depends(admin), db: Session = Depends(get_db)
):
    """Why: the admin pastes outside reviews (Google, Facebook) to set a fair starting score.
    Then: the result (app/ai/sentiment.py) feeds the approve checklist."""
    raise not_implemented(OWNER)
