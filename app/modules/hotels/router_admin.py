"""Feature A3 (hotels part) · Admin hotels. Owner: Person 5."""

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.hotels.schemas import HotelIn, HotelUpdateIn

router = APIRouter(prefix="/admin/hotels", tags=["A3 · Admin hotels"])
OWNER = "Person 5"
admin = require_role("admin")


@router.get("")
def list_hotels(user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin sees every hotel with how many offers it has and its lowest price."""
    raise not_implemented(OWNER)


@router.post("", status_code=201)
def add_hotel(body: HotelIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: companies can only sell hotels that exist, so the admin adds them first.
    Then: companies can attach offers to it (Person 6)."""
    raise not_implemented(OWNER)


@router.patch("/{hotel_id}")
def update_hotel(hotel_id: int, body: HotelUpdateIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: fix name, stars, location or amenities."""
    raise not_implemented(OWNER)


@router.delete("/{hotel_id}", status_code=204)
def delete_hotel(hotel_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: remove a closed hotel (only when it has no active offers)."""
    raise not_implemented(OWNER)


@router.post("/import", status_code=201)
async def import_hotels(file: UploadFile, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: typing 30-50 hotels by hand is slow, so the seed comes from a CSV.
    Then: fills Cairo, Luxor and Aswan in minutes."""
    raise not_implemented(OWNER)
