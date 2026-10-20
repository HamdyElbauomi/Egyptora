"""Company logic shared by the portal, admin and public routes."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.sentiment import complaints_of
from app.modules.accounts.models import User
from app.modules.companies.models import Company, Review
from app.modules.companies.schemas import (
    CompanyAdminOut,
    CompanyOut,
    CompanyPublicOut,
    ReviewInsightsOut,
    ReviewOut,
)
from app.modules.companies.trust import trust_score
from app.modules.offers.models import Offer


def company_of(db: Session, user: User) -> Company:
    """The company owned by the logged-in company user."""
    company = db.scalar(select(Company).where(Company.owner_user_id == user.id))
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No company is linked to this account")
    return company


def get_company_or_404(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Company {company_id} not found")
    return company


def require_status(company: Company, *allowed: str) -> None:
    """Moves between states are only allowed from certain states, e.g. reject only a pending company."""
    if company.status not in allowed:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Company is {company.status}; this action needs it to be {' or '.join(allowed)}",
        )


def average_rating(db: Session, company_id: int) -> tuple[int, float | None]:
    count, avg = db.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(Review.company_id == company_id)
    ).one()
    return int(count), (float(avg) if avg is not None else None)


def recompute_trust(db: Session, company: Company) -> None:
    """trust = (10 × initial + n × average rating) ÷ (10 + n). See trust.py."""
    if company.initial_score is None:
        return
    count, avg = average_rating(db, company.id)
    company.reviews_count = count
    company.trust_score = trust_score(float(company.initial_score), count, avg)


def to_out(company: Company) -> CompanyOut:
    return CompanyOut.model_validate(company)


def to_admin_out(db: Session, company: Company) -> CompanyAdminOut:
    owner = db.get(User, company.owner_user_id)
    active = db.scalar(select(func.count(Offer.id)).where(Offer.company_id == company.id, Offer.status == "active"))
    return CompanyAdminOut(
        **to_out(company).model_dump(),
        owner_user_id=company.owner_user_id,
        owner_name=owner.name if owner else "",
        owner_email=owner.email if owner else "",
        active_offers=int(active or 0),
        approved_by=company.approved_by,
    )


def to_public_out(company: Company) -> CompanyPublicOut:
    return CompanyPublicOut(
        id=company.id,
        name=company.name,
        trust_score=float(company.trust_score) if company.trust_score is not None else None,
        reviews_count=company.reviews_count,
        years_active=company.years_active,
        google_rating=float(company.google_rating) if company.google_rating is not None else None,
        website=company.website,
        facebook_url=company.facebook_url,
        instagram_url=company.instagram_url,
    )


# ---------- reviews ----------


def reviews_query(company_id: int):
    """Reviews of a company with the reviewer's name, newest first."""
    return (
        select(Review, User.name)
        .join(User, User.id == Review.user_id)
        .where(Review.company_id == company_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    )


def to_review_out(review: Review, reviewer_name: str) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        company_id=review.company_id,
        rating=review.rating,
        comment=review.comment,
        sentiment=review.sentiment,
        reviewer_name=(reviewer_name or "Traveler").split()[0],
        created_at=review.created_at,
    )


def trips_with_company(db: Session, user_id: int, company_id: int) -> list[int]:
    """The traveler's trips where at least one night is booked with this company's offer, newest first."""
    from app.modules.trips.models import Trip, TripDay  # local import: trips depends on companies

    return list(
        db.scalars(
            select(Trip.id)
            .join(TripDay, TripDay.trip_id == Trip.id)
            .join(Offer, Offer.id == TripDay.offer_id)
            .where(Trip.user_id == user_id, Offer.company_id == company_id)
            .group_by(Trip.id)
            .order_by(func.max(Trip.created_at).desc(), Trip.id.desc())
        )
    )


def review_insights(db: Session, company: Company) -> ReviewInsightsOut:
    rows = db.execute(reviews_query(company.id)).all()
    reviews = [r for r, _ in rows]
    counts = {str(n): sum(1 for r in reviews if r.rating == n) for n in range(1, 6)}
    sentiments = {s: sum(1 for r in reviews if r.sentiment == s) for s in ("positive", "neutral", "negative")}
    with_comment = sum(sentiments.values())
    unhappy = [r.comment for r in reviews if r.comment and r.sentiment in ("negative", "neutral")]
    _, avg = average_rating(db, company.id)
    return ReviewInsightsOut(
        reviews_count=len(reviews),
        average_rating=round(avg, 2) if avg is not None else None,
        rating_counts=counts,
        sentiment_counts=sentiments,
        positive_share=round(sentiments["positive"] / with_comment, 3) if with_comment else None,
        top_complaints=complaints_of(unhappy),
        trust_score=float(company.trust_score) if company.trust_score is not None else None,
        initial_score=float(company.initial_score) if company.initial_score is not None else None,
        recent_negative=[to_review_out(r, name) for r, name in rows if r.sentiment == "negative"][:3],
    )
