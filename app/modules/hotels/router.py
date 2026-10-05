"""Feature T7 · Hotel search in plain language. Owner: Person 5."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, not_implemented
from app.modules.accounts.models import User
from app.modules.hotels.schemas import HotelSearchIn

router = APIRouter(prefix="/hotels", tags=["T7 · Hotel search"])
OWNER = "Person 5"


@router.post("/search")
def search_hotels(body: HotelSearchIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """AI. Why: travelers ask like people do: "4-star in Luxor under 1500 near the Nile with free cancellation".
    Then: calls app/ai/nl2sql.py, runs the SQL on a READ-ONLY connection (settings.readonly_database_url),
    logs the question in nl_queries. If the SQL fails, fall back to the filter search below."""
    raise not_implemented(OWNER)


@router.get("")
def filter_hotels(
    city_id: int | None = None,
    stars: int | None = None,
    max_price: int | None = None,
    db: Session = Depends(get_db),
):
    """Why: normal filters work without AI and are the fallback when AI search fails.
    Then: same results card as /hotels/search."""
    raise not_implemented(OWNER)


@router.get("/{hotel_id}")
def hotel_detail(hotel_id: int, db: Session = Depends(get_db)):
    """Why: the traveler opens a hotel to see details.
    Then: the offers list inside it comes from Person 6 (GET /hotels/{id}/offers)."""
    raise not_implemented(OWNER)
