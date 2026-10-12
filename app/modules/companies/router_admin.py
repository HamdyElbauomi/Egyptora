"""Feature A2 · Companies, verification and trust (admin).

A company moves through these states:
    pending --approve--> approved --suspend--> suspended --approve--> approved
    pending --reject---> rejected --(company uploads a new license)--> pending
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.ai.sentiment import analyze
from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate
from app.modules.accounts.models import User
from app.modules.companies.models import COMPANY_STATUSES, Company
from app.modules.companies.schemas import (
    AnalyzeReviewsIn,
    AnalyzeReviewsOut,
    ApproveChecklistIn,
    ApproveOut,
    CompanyAdminOut,
    RejectIn,
    SuspendOut,
)
from app.modules.companies.service import get_company_or_404, recompute_trust, require_status, to_admin_out
from app.modules.companies.trust import initial_score_from_checklist
from app.modules.offers.service import pause_all_for_company

router = APIRouter(prefix="/admin/companies", tags=["A2 · Admin companies"])
admin = require_role("admin")


@router.get("", response_model=Page[CompanyAdminOut])
def list_companies(
    status_filter: str | None = Query(None, alias="status", pattern=f"^({'|'.join(COMPANY_STATUSES)})$"),
    params: PageParams = Depends(),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> Page[CompanyAdminOut]:
    """Why: the admin needs a queue of companies waiting for approval. Pending ones come first, oldest first.
    Then: opens one company in GET /admin/companies/{id}."""
    pending_first = case((Company.status == "pending", 0), else_=1)
    stmt = select(Company).order_by(pending_first, Company.created_at, Company.id)
    if status_filter:
        stmt = stmt.where(Company.status == status_filter)
    companies, total = paginate(db, stmt, params)
    return Page(data=[to_admin_out(db, c) for c in companies], page=params.page, limit=params.limit, total=total)


@router.get("/{company_id}", response_model=CompanyAdminOut)
def company_detail(company_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> CompanyAdminOut:
    """Why: the admin checks the license file, social pages and activity before deciding.
    Then: approve, reject or suspend."""
    return to_admin_out(db, get_company_or_404(db, company_id))


@router.post("/{company_id}/approve", response_model=ApproveOut)
def approve(
    company_id: int, body: ApproveChecklistIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> ApproveOut:
    """Why: the checklist gives a starting trust score before any traveler reviews exist.
    How: initial_score comes from the checklist (trust.py) and counts as 10 reviews in the trust formula.
    Works on pending companies, and on suspended ones to lift a suspension.
    Then: the company can publish offers, and its trust score shows next to them."""
    company = get_company_or_404(db, company_id)
    require_status(company, "pending", "suspended")
    if not body.license_verified:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can't approve without a verified license")
    initial = initial_score_from_checklist(
        body.license_verified, body.google_rating, body.years_active, body.social_presence
    )
    company.google_rating = body.google_rating
    company.years_active = body.years_active
    company.initial_score = initial
    recompute_trust(db, company)
    company.status = "approved"
    company.reject_reason = None
    company.approved_by = user.id
    company.approved_at = datetime.now(UTC)
    db.commit()
    db.refresh(company)
    return ApproveOut(company=to_admin_out(db, company), initial_score=initial, trust_score=float(company.trust_score))


@router.post("/{company_id}/reject", response_model=CompanyAdminOut)
def reject(
    company_id: int, body: RejectIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> CompanyAdminOut:
    """Why: unlicensed or fake companies must be kept out. Only pending companies can be rejected.
    Then: the company sees the reason in GET /company/me and can upload a new license to try again."""
    company = get_company_or_404(db, company_id)
    require_status(company, "pending")
    company.status = "rejected"
    company.reject_reason = body.reason
    db.commit()
    db.refresh(company)
    return to_admin_out(db, company)


@router.post("/{company_id}/suspend", response_model=SuspendOut)
def suspend(company_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> SuspendOut:
    """Why: a company that cheats travelers must be stopped fast. Only approved companies can be suspended.
    Effect: every active offer of the company is paused, so travelers stop seeing it.
    Then: approve it again to lift the suspension (its offers stay paused until the company resumes them)."""
    company = get_company_or_404(db, company_id)
    require_status(company, "approved")
    paused = pause_all_for_company(db, company.id)
    company.status = "suspended"
    db.commit()
    db.refresh(company)
    return SuspendOut(company=to_admin_out(db, company), paused_offers=paused)


@router.post("/{company_id}/analyze-reviews", response_model=AnalyzeReviewsOut)
def analyze_reviews(
    company_id: int, body: AnalyzeReviewsIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> AnalyzeReviewsOut:
    """AI. Why: the admin pastes outside reviews (Google, Facebook) to judge a company fairly before approving.
    Returns sentiment per review, % positive, top complaints, and a suggested 0-5 social_presence.
    Then: the admin uses it in the approve checklist."""
    get_company_or_404(db, company_id)
    result = analyze(body.reviews)
    suggested = round(result.positive_share * 5)
    return AnalyzeReviewsOut(**result.model_dump(), suggested_social_presence=suggested)
