"""Feature T9 · Company profile and reviews (traveler side)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.sentiment import analyze
from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate_rows
from app.modules.accounts.models import User
from app.modules.companies.models import Review
from app.modules.companies.schemas import CompanyPublicOut, ReviewAddedOut, ReviewIn, ReviewOut
from app.modules.companies.service import (
    get_company_or_404,
    recompute_trust,
    reviews_query,
    to_public_out,
    to_review_out,
    trips_with_company,
)

router = APIRouter(prefix="/companies", tags=["T9 · Company reviews"])


@router.get("/{company_id}", response_model=CompanyPublicOut)
def company_profile(company_id: int, db: Session = Depends(get_db)) -> CompanyPublicOut:
    """Why: travelers decide which offer to trust partly by company reputation. Public, no login.
    Only approved companies are visible; pending, rejected or suspended ones return 404.
    Then: shown next to each offer in the hotel's offer list."""
    return to_public_out(get_public_company(db, company_id))


def get_public_company(db: Session, company_id: int):
    company = get_company_or_404(db, company_id)
    if company.status != "approved":
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Company {company_id} not found")
    return company


@router.get("/{company_id}/reviews", response_model=Page[ReviewOut])
def company_reviews(company_id: int, params: PageParams = Depends(), db: Session = Depends(get_db)) -> Page[ReviewOut]:
    """Why: travelers read what others said before choosing, newest first. Public, no login.
    Only the reviewer's first name is shown."""
    get_public_company(db, company_id)
    rows, total = paginate_rows(db, reviews_query(company_id), params)
    return Page(data=[to_review_out(*r) for r in rows], page=params.page, limit=params.limit, total=total)


@router.post("/{company_id}/reviews", status_code=201, response_model=ReviewAddedOut)
def add_review(
    company_id: int, body: ReviewIn, user: User = Depends(require_role("traveler")), db: Session = Depends(get_db)
) -> ReviewAddedOut:
    """Why: after the trip, the traveler rates the company, and the rating moves its trust score.
    Rules: only travelers who booked a night with this company in one of their trips can review it
    (403 otherwise), once per trip (409). Without trip_id, the latest such trip is used.
    The comment gets a sentiment (app/ai/sentiment.py), and trust is recalculated:
    (10 × initial + n × average rating) ÷ (10 + n)."""
    company = get_public_company(db, company_id)
    eligible = trips_with_company(db, user.id, company.id)
    if body.trip_id is not None:
        if body.trip_id not in eligible:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "That trip has no night booked with this company (or it isn't yours)"
            )
        trip_id = body.trip_id
    elif eligible:
        trip_id = eligible[0]
    else:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "You can review a company after choosing its offer in one of your trips"
        )
    exists = db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.company_id == company.id, Review.trip_id == trip_id)
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already reviewed this company for that trip")

    comment = (body.comment or "").strip() or None
    sentiment = analyze([comment]).items[0] if comment else None
    review = Review(
        company_id=company.id,
        user_id=user.id,
        trip_id=trip_id,
        rating=body.rating,
        comment=comment,
        sentiment=sentiment.sentiment if sentiment else None,
        sentiment_score=sentiment.score if sentiment else None,
    )
    db.add(review)
    db.flush()
    recompute_trust(db, company)
    db.commit()
    db.refresh(review)
    return ReviewAddedOut(
        review=to_review_out(review, user.name),
        trust_score=float(company.trust_score) if company.trust_score is not None else None,
        reviews_count=company.reviews_count,
    )
