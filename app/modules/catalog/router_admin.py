"""Feature A4 (cities and interests part) · Catalog basics. Owner: Person 3."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.catalog.schemas import CityIn, CityUpdateIn, InterestIn, InterestUpdateIn

router = APIRouter(prefix="/admin", tags=["A4 · Admin cities and interests"])
OWNER = "Person 3"
admin = require_role("admin")


@router.post("/cities", status_code=201)
def add_city(body: CityIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: Egyptora grows beyond Cairo, Luxor and Aswan.
    Then: the new city appears in preferences (Person 2) and hotels (Person 5)."""
    raise not_implemented(OWNER)


@router.patch("/cities/{city_id}")
def update_city(city_id: int, body: CityUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: fix a city's description or photo."""
    raise not_implemented(OWNER)


@router.post("/interests", status_code=201)
def add_interest(body: InterestIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: add a new interest chip (for example "Diving").
    Then: shows in preference step 1 and can tag places (Person 4)."""
    raise not_implemented(OWNER)


@router.patch("/interests/{interest_id}")
def update_interest(
    interest_id: int, body: InterestUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)
):
    """Why: rename or change an interest's icon."""
    raise not_implemented(OWNER)
