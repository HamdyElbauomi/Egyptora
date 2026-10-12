"""Company logic shared by the portal, admin and public routes."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.accounts.models import User
from app.modules.companies.models import Company, Review
from app.modules.companies.schemas import CompanyAdminOut, CompanyOut, CompanyPublicOut
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
