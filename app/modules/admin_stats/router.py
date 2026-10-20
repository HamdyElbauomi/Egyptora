"""Feature A1 · Admin overview. Owner: Person 3."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.accounts.models import User
from app.modules.admin_stats.schemas import (
    AIStats,
    CatalogStats,
    CompanyStats,
    NeedsAttention,
    OfferStats,
    ReviewStats,
    StatsOut,
    TripStats,
    UserStats,
)
from app.modules.ai_quality.models import NLQuery
from app.modules.ai_quality.router_admin import build_metrics
from app.modules.catalog.models import City
from app.modules.companies.models import Company, Review
from app.modules.hotels.models import Hotel
from app.modules.offers.models import Offer
from app.modules.offers.router_admin import LOW_PRICE_RATIO
from app.modules.offers.service import market_median
from app.modules.places.models import Place
from app.modules.trips.models import Trip, TripDay

router = APIRouter(prefix="/admin", tags=["A1 · Admin overview"])


def grouped(db: Session, column) -> dict[str, int]:
    return {k: int(v) for k, v in db.execute(select(column, func.count()).group_by(column)).all()}


def count(db: Session, stmt) -> int:
    return int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)


def rounded(value, digits: int = 1) -> float | None:
    return round(float(value), digits) if value is not None else None


@router.get("/stats", response_model=StatsOut)
def stats(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> StatsOut:
    """Why: the admin's first screen needs the health of the platform at a glance:
    users, trips built, companies by status, offers, catalog size, reviews, AI quality,
    and a needs_attention to-do list (pending companies, suspiciously cheap offers, scans to review,
    failed searches not fixed yet). Read-only counts from everyone's tables."""
    week_ago = datetime.now(UTC) - timedelta(days=7)
    roles = grouped(db, User.role)
    trip_status = grouped(db, Trip.status)
    companies = grouped(db, Company.status)
    offers = grouped(db, Offer.status)
    avg_days, avg_cost = db.execute(select(func.avg(Trip.days), func.avg(Trip.total_cost))).one()
    reviews_total, avg_rating = db.execute(select(func.count(Review.id), func.avg(Review.rating))).one()
    metrics = build_metrics(db)

    active_offers = list(db.scalars(select(Offer).where(Offer.status == "active")))
    low_price = 0
    for offer in active_offers:
        median = market_median(db, offer)
        if median and offer.price_per_night < LOW_PRICE_RATIO * median:
            low_price += 1

    return StatsOut(
        users=UserStats(
            travelers=roles.get("traveler", 0),
            company_accounts=roles.get("company", 0),
            admins=roles.get("admin", 0),
            new_last_7_days=count(db, select(User.id).where(User.created_at >= week_ago)),
        ),
        trips=TripStats(
            total=sum(trip_status.values()),
            saved=trip_status.get("saved", 0),
            drafts=trip_status.get("draft", 0),
            shared=count(db, select(Trip.id).where(Trip.share_token.is_not(None))),
            created_last_7_days=count(db, select(Trip.id).where(Trip.created_at >= week_ago)),
            avg_days=rounded(avg_days),
            avg_total_cost=rounded(avg_cost, 0),
        ),
        companies=CompanyStats(
            pending=companies.get("pending", 0),
            approved=companies.get("approved", 0),
            rejected=companies.get("rejected", 0),
            suspended=companies.get("suspended", 0),
        ),
        offers=OfferStats(
            active=offers.get("active", 0),
            paused=offers.get("paused", 0),
            flagged=offers.get("flagged", 0),
            hotels_with_offers=count(db, select(Offer.hotel_id).where(Offer.status == "active").distinct()),
            nights_booked_in_trips=count(db, select(TripDay.id).where(TripDay.offer_id.is_not(None))),
        ),
        catalog=CatalogStats(
            cities=count(db, select(City.id)), places=count(db, select(Place.id)), hotels=count(db, select(Hotel.id))
        ),
        reviews=ReviewStats(total=int(reviews_total), average_rating=rounded(avg_rating, 2)),
        ai=AIStats(
            search_success_rate=metrics.search.success_rate,
            scan_recognition_rate=round(metrics.scans.recognized / metrics.scans.total, 3)
            if metrics.scans.total
            else None,
            chat_keep_rate=metrics.chat.keep_rate,
        ),
        needs_attention=NeedsAttention(
            pending_companies=companies.get("pending", 0),
            low_price_offers=low_price,
            scans_to_review=metrics.scans.waiting_review,
            failed_searches=count(
                db, select(NLQuery.id).where(NLQuery.status == "failed", NLQuery.fixed_sql.is_(None))
            ),
        ),
    )
