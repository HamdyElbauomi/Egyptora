"""Feature A1 · Admin overview. Owner: Person 3."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User

router = APIRouter(prefix="/admin", tags=["A1 · Admin overview"])
OWNER = "Person 3"


@router.get("/stats")
def stats(user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    """Why: the admin's first screen needs the health of the platform at a glance:
    travelers, trips built, companies pending, active offers, NL-to-SQL success rate, scan accuracy.
    Then: pulls counts from everyone's tables (read-only)."""
    raise not_implemented(OWNER)
