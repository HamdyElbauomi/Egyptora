"""Feature A4 (cities and interests part) · Catalog basics (admin)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_role
from app.modules.accounts.models import User
from app.modules.catalog.models import City, Interest
from app.modules.catalog.schemas import CityIn, CityOut, CityUpdateIn, InterestIn, InterestOut, InterestUpdateIn
from app.modules.catalog.service import ensure_unique_name, get_city_or_404, get_interest_or_404

router = APIRouter(prefix="/admin", tags=["A4 · Admin cities and interests"])
admin = require_role("admin")


@router.post("/cities", response_model=CityOut, status_code=201)
def add_city(body: CityIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> City:
    """Why: Egyptora grows beyond Cairo, Luxor and Aswan.
    Then: the new city appears in preferences (GET /cities) and can hold places and hotels."""
    ensure_unique_name(db, City, body.name)
    city = City(**body.model_dump())
    city.name = body.name.strip()
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


@router.patch("/cities/{city_id}", response_model=CityOut)
def update_city(city_id: int, body: CityUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> City:
    """Why: fix a city's description or photo. Only the fields you send are changed."""
    city = get_city_or_404(db, city_id)
    changes = body.model_dump(exclude_unset=True)
    if "name" in changes:
        ensure_unique_name(db, City, changes["name"], exclude_id=city_id)
        changes["name"] = changes["name"].strip()
    for field, value in changes.items():
        setattr(city, field, value)
    db.commit()
    db.refresh(city)
    return city


@router.post("/interests", response_model=InterestOut, status_code=201)
def add_interest(body: InterestIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> Interest:
    """Why: add a new interest chip (for example "Diving").
    Then: shows in preference step 1 and can tag places."""
    ensure_unique_name(db, Interest, body.name)
    interest = Interest(name=body.name.strip(), icon=body.icon)
    db.add(interest)
    db.commit()
    db.refresh(interest)
    return interest


@router.patch("/interests/{interest_id}", response_model=InterestOut)
def update_interest(
    interest_id: int, body: InterestUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)
) -> Interest:
    """Why: rename an interest or change its icon. Only the fields you send are changed."""
    interest = get_interest_or_404(db, interest_id)
    changes = body.model_dump(exclude_unset=True)
    if "name" in changes:
        ensure_unique_name(db, Interest, changes["name"], exclude_id=interest_id)
        changes["name"] = changes["name"].strip()
    for field, value in changes.items():
        setattr(interest, field, value)
    db.commit()
    db.refresh(interest)
    return interest
