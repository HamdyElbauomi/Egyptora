"""Features C3, C4 · Company offers, dashboard and competition.

Every route needs role=company. Managing offers also needs the company to be approved (403 otherwise),
but reading the dashboard and alerts works in any state.
"""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams
from app.modules.accounts.models import User
from app.modules.companies.service import company_of
from app.modules.hotels.models import Hotel
from app.modules.hotels.schemas import HotelCardOut
from app.modules.hotels.service import cards_query, to_card
from app.modules.offers.models import OFFER_STATUSES, Offer, PriceAlert
from app.modules.offers.schemas import (
    AlertOut,
    CompetitorOut,
    DashboardOut,
    MarketOut,
    MyOfferOut,
    OfferImportOut,
    OfferIn,
    OfferUpdateIn,
)
from app.modules.offers.service import (
    approved_company_of,
    best_value_rank,
    create_undercut_alerts,
    ensure_hotel_exists,
    ensure_room_free,
    get_own_offer,
    live_competition,
    position_of,
    to_my_out,
)
from app.modules.trips.models import TripDay

router = APIRouter(prefix="/company", tags=["C3-C4 · Company offers"])
company_role = require_role("company")
MAX_CSV_BYTES = 2 * 1024 * 1024


@router.get("/hotels", response_model=Page[HotelCardOut])
def hotels_to_sell(
    search: str | None = Query(None, description="Part of the hotel name"),
    city_id: int | None = None,
    params: PageParams = Depends(),
    user: User = Depends(company_role),
    db: Session = Depends(get_db),
) -> Page[HotelCardOut]:
    """Why: a company needs to find the hotel it wants to sell, with the current lowest price to beat.
    Then: picks one and creates an offer with POST /company/offers."""
    stmt, _ = cards_query()
    stmt = stmt.order_by(Hotel.city_id, Hotel.name)
    if city_id is not None:
        stmt = stmt.where(Hotel.city_id == city_id)
    if search:
        stmt = stmt.where(func.lower(Hotel.name).contains(search.lower()))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.execute(stmt.offset(params.offset).limit(params.limit)).all()
    return Page(data=[to_card(*r) for r in rows], page=params.page, limit=params.limit, total=int(total or 0))


@router.get("/offers", response_model=list[MyOfferOut])
def my_offers(
    status_filter: str | None = Query(None, alias="status", pattern=f"^({'|'.join(OFFER_STATUSES)})$"),
    user: User = Depends(company_role),
    db: Session = Depends(get_db),
) -> list[MyOfferOut]:
    """Why: the company manages all its offers in one list, each with its position against competitors.
    Then: edit, pause, resume or delete from here."""
    company = company_of(db, user)
    stmt = select(Offer).where(Offer.company_id == company.id).order_by(Offer.hotel_id, Offer.room_type)
    if status_filter:
        stmt = stmt.where(Offer.status == status_filter)
    return [to_my_out(db, o) for o in db.scalars(stmt)]


@router.post("/offers", response_model=MyOfferOut, status_code=201)
def create_offer(body: OfferIn, user: User = Depends(company_role), db: Session = Depends(get_db)) -> MyOfferOut:
    """Why: the company sets its own price, room type and cancellation terms for a hotel.
    Effect: competitors whose price is now higher get an "undercut" alert.
    Then: the offer shows on the hotel page next to other companies' offers."""
    company = approved_company_of(db, user)
    ensure_hotel_exists(db, body.hotel_id)
    ensure_room_free(db, company.id, body.hotel_id, body.room_type)
    offer = Offer(company_id=company.id, **body.model_dump())
    offer.room_type = body.room_type.strip()
    db.add(offer)
    db.flush()
    create_undercut_alerts(db, offer, old_price=None)
    db.commit()
    db.refresh(offer)
    return to_my_out(db, offer)


@router.patch("/offers/{offer_id}", response_model=MyOfferOut)
def update_offer(
    offer_id: int, body: OfferUpdateIn, user: User = Depends(company_role), db: Session = Depends(get_db)
) -> MyOfferOut:
    """Why: prices change with the season and the competition. Only the fields you send are changed.
    Effect: lowering the price alerts competitors you just went below."""
    company = approved_company_of(db, user)
    offer = get_own_offer(db, company, offer_id)
    changes = body.model_dump(exclude_unset=True)
    if "room_type" in changes:
        if changes["room_type"] is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "room_type can't be empty")
        ensure_room_free(db, company.id, offer.hotel_id, changes["room_type"], exclude_id=offer_id)
    if changes.get("price_per_night", 1) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "price_per_night can't be empty")
    new_from = changes.get("valid_from", offer.valid_from)
    new_to = changes.get("valid_to", offer.valid_to)
    if new_from and new_to and new_to < new_from:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "valid_to must be on or after valid_from")
    old_price = offer.price_per_night
    for field, value in changes.items():
        setattr(offer, field, value)
    db.flush()
    if offer.price_per_night < old_price:
        create_undercut_alerts(db, offer, old_price=old_price)
    db.commit()
    db.refresh(offer)
    return to_my_out(db, offer)


@router.post("/offers/{offer_id}/pause", response_model=MyOfferOut)
def pause_offer(offer_id: int, user: User = Depends(company_role), db: Session = Depends(get_db)) -> MyOfferOut:
    """Why: the hotel is full or the deal ended, but the company wants to keep the offer for later.
    Then: hidden from travelers, search and the trip planner until resumed."""
    offer = get_own_offer(db, approved_company_of(db, user), offer_id)
    if offer.status != "active":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Only active offers can be paused (this one is {offer.status})")
    offer.status = "paused"
    db.commit()
    db.refresh(offer)
    return to_my_out(db, offer)


@router.post("/offers/{offer_id}/resume", response_model=MyOfferOut)
def resume_offer(offer_id: int, user: User = Depends(company_role), db: Session = Depends(get_db)) -> MyOfferOut:
    """Why: the room is available again. Flagged offers can't be resumed until the admin clears the flag,
    and an offer whose valid_to has passed needs new dates first."""
    offer = get_own_offer(db, approved_company_of(db, user), offer_id)
    if offer.status != "paused":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Only paused offers can be resumed (this one is {offer.status})")
    if offer.valid_to and offer.valid_to < date.today():
        raise HTTPException(status.HTTP_409_CONFLICT, "This offer has expired; update valid_to first")
    offer.status = "active"
    db.flush()
    create_undercut_alerts(db, offer, old_price=None)
    db.commit()
    db.refresh(offer)
    return to_my_out(db, offer)


@router.delete("/offers/{offer_id}", status_code=204)
def delete_offer(offer_id: int, user: User = Depends(company_role), db: Session = Depends(get_db)) -> None:
    """Why: remove an offer for good. Trip nights that had chosen it keep the night with no hotel."""
    offer = get_own_offer(db, company_of(db, user), offer_id)
    db.delete(offer)
    db.commit()


@router.post("/offers/import", response_model=OfferImportOut, status_code=201)
async def import_offers(
    file: UploadFile = File(
        ...,
        description="CSV columns: hotel_id, room_type, price_per_night, breakfast_included, "
        "free_cancellation, cancellation_days, valid_from, valid_to (dates as YYYY-MM-DD)",
    ),
    user: User = Depends(company_role),
    db: Session = Depends(get_db),
) -> OfferImportOut:
    """Why: companies with many hotels upload a CSV instead of typing each offer.
    A row for a hotel and room type you already sell updates that offer; any other row creates one.
    All or nothing: one bad row and nothing is saved (400 lists every error)."""
    company = approved_company_of(db, user)
    raw = await file.read()
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV is larger than 2 MB")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    except UnicodeDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The file must be a UTF-8 CSV") from exc
    missing = {"hotel_id", "room_type", "price_per_night"} - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Missing required columns: {sorted(missing)}")

    hotel_ids = set(db.scalars(select(Hotel.id)))
    truthy = {"1", "true", "yes", "y"}
    parsed, errors = [], []
    for line, rec in enumerate(reader, start=2):
        try:
            row = OfferIn(
                hotel_id=int(rec["hotel_id"]),
                room_type=(rec.get("room_type") or "").strip(),
                price_per_night=int(rec["price_per_night"]),
                breakfast_included=(rec.get("breakfast_included") or "").strip().lower() in truthy,
                free_cancellation=(rec.get("free_cancellation") or "").strip().lower() in truthy,
                cancellation_days=int(rec["cancellation_days"]) if rec.get("cancellation_days") else None,
                valid_from=rec.get("valid_from") or None,
                valid_to=rec.get("valid_to") or None,
            )
        except (ValueError, ValidationError) as exc:
            errors.append({"row": line, "error": " ".join(str(exc).splitlines()[:3])})
            continue
        if row.hotel_id not in hotel_ids:
            errors.append({"row": line, "error": f"Unknown hotel_id {row.hotel_id}"})
            continue
        parsed.append(row)
    if errors:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            {"message": f"{len(errors)} rows have errors; nothing was imported", "errors": errors},
        )

    mine = {
        (o.hotel_id, o.room_type.lower()): o for o in db.scalars(select(Offer).where(Offer.company_id == company.id))
    }
    created = updated = 0
    for row in parsed:
        existing = mine.get((row.hotel_id, row.room_type.lower()))
        if existing:
            old_price = existing.price_per_night
            for field, value in row.model_dump(exclude={"hotel_id", "room_type"}).items():
                setattr(existing, field, value)
            db.flush()
            if existing.price_per_night < old_price:
                create_undercut_alerts(db, existing, old_price=old_price)
            updated += 1
        else:
            offer = Offer(company_id=company.id, **row.model_dump())
            db.add(offer)
            db.flush()
            create_undercut_alerts(db, offer, old_price=None)
            mine[(row.hotel_id, row.room_type.lower())] = offer
            created += 1
    db.commit()
    return OfferImportOut(created=created, updated=updated)


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(user: User = Depends(company_role), db: Session = Depends(get_db)) -> DashboardOut:
    """Why: the company's first screen: offers by status, how many are the cheapest, how often travelers
    chose them, trust score and unread alerts. Works in any company status."""
    company = company_of(db, user)
    offers = list(db.scalars(select(Offer).where(Offer.company_id == company.id)))
    by_status = {s: sum(1 for o in offers if o.status == s) for s in OFFER_STATUSES}
    cheapest = 0
    for offer in offers:
        if offer.status == "active":
            position, _, _ = position_of(offer, live_competition(db, offer.hotel_id, offer.room_type))
            cheapest += position == 1
    chosen = db.scalar(
        select(func.count(TripDay.id)).join(Offer, Offer.id == TripDay.offer_id).where(Offer.company_id == company.id)
    )
    unread = db.scalar(
        select(func.count(PriceAlert.id)).where(PriceAlert.company_id == company.id, PriceAlert.is_read.is_(False))
    )
    return DashboardOut(
        status=company.status,
        trust_score=float(company.trust_score) if company.trust_score is not None else None,
        reviews_count=company.reviews_count,
        active_offers=by_status["active"],
        paused_offers=by_status["paused"],
        flagged_offers=by_status["flagged"],
        cheapest_in_market=cheapest,
        times_chosen=int(chosen or 0),
        unread_alerts=int(unread or 0),
    )


@router.get("/offers/{offer_id}/market", response_model=MarketOut)
def offer_market(offer_id: int, user: User = Depends(company_role), db: Session = Depends(get_db)) -> MarketOut:
    """Why: the company wants to know "am I the cheapest?" for this hotel and room type: position (#3 of 4),
    lowest price, how far above it they are, and Best value rank. Competitor names are shown, as travelers see them.
    Then: pushes companies to lower prices or improve terms, which is the competition."""
    company = company_of(db, user)
    offer = get_own_offer(db, company, offer_id)
    competition = live_competition(db, offer.hotel_id, offer.room_type)
    position, total, lowest = position_of(offer, competition)
    lowest = lowest if lowest is not None else offer.price_per_night
    return MarketOut(
        offer_id=offer.id,
        hotel_name=db.scalar(select(Hotel.name).where(Hotel.id == offer.hotel_id)),
        room_type=offer.room_type,
        my_price=offer.price_per_night,
        position=position,
        total=total,
        lowest_price=lowest,
        gap_to_lowest=max(offer.price_per_night - lowest, 0),
        best_value_rank=best_value_rank(offer, competition),
        competitors=[
            CompetitorOut(
                company_name=c.name,
                price_per_night=o.price_per_night,
                free_cancellation=o.free_cancellation,
                breakfast_included=o.breakfast_included,
                trust_score=float(c.trust_score) if c.trust_score is not None else None,
                is_mine=o.company_id == company.id,
            )
            for o, c in competition
        ],
    )


@router.get("/alerts", response_model=list[AlertOut])
def alerts(
    unread_only: bool = False, user: User = Depends(company_role), db: Session = Depends(get_db)
) -> list[PriceAlert]:
    """Why: the company should know right away when a competitor goes lower or the admin flags its price.
    Unread alerts first, newest first. Then: react with PATCH /company/offers/{id}."""
    company = company_of(db, user)
    stmt = (
        select(PriceAlert)
        .where(PriceAlert.company_id == company.id)
        .order_by(PriceAlert.is_read, PriceAlert.created_at.desc(), PriceAlert.id.desc())
    )
    if unread_only:
        stmt = stmt.where(PriceAlert.is_read.is_(False))
    return list(db.scalars(stmt))


@router.post("/alerts/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(alert_id: int, user: User = Depends(company_role), db: Session = Depends(get_db)) -> PriceAlert:
    """Why: clear alerts already seen."""
    company = company_of(db, user)
    alert = db.get(PriceAlert, alert_id)
    if alert is None or alert.company_id != company.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Alert {alert_id} not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
