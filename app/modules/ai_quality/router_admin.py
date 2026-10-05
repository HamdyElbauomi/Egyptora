"""Feature A5 (search part) · AI quality: metrics, failed queries, training examples. Owner: Person 5."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import not_implemented, require_role
from app.modules.accounts.models import User
from app.modules.hotels.schemas import FixSqlIn

router = APIRouter(prefix="/admin/ai", tags=["A5 · Admin AI quality"])
OWNER = "Person 5"
admin = require_role("admin")


@router.get("/metrics")
def ai_metrics(user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the team needs to prove the AI works: search success rate, speed, unsure scans.
    Then: numbers for the admin dashboard and for the graduation report."""
    raise not_implemented(OWNER)


@router.get("/queries")
def list_queries(status: str | None = "failed", user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin reviews questions the search got wrong."""
    raise not_implemented(OWNER)


@router.post("/queries/{query_id}/fix")
def fix_query(query_id: int, body: FixSqlIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: the admin writes the correct SQL and tests it (read-only connection).
    Then: saved as fixed_sql, ready for add-to-training."""
    raise not_implemented(OWNER)


@router.post("/queries/{query_id}/add-to-training", status_code=201)
def add_to_training(query_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: a fixed mistake should never happen again.
    Then: question + fixed SQL become a training example sent with every nl2sql call."""
    raise not_implemented(OWNER)


@router.get("/training-examples")
def list_training_examples(user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: see what the model is learning from."""
    raise not_implemented(OWNER)


@router.delete("/training-examples/{example_id}", status_code=204)
def delete_training_example(example_id: int, user: User = Depends(admin), db: Session = Depends(get_db)):
    """Why: remove a wrong or outdated example so it stops misleading nl2sql."""
    raise not_implemented(OWNER)
