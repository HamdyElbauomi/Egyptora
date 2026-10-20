"""Feature A5 (search part) · AI quality: metrics, failed queries, training examples. Owner: Person 5."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_role
from app.core.pagination import Page, PageParams, paginate
from app.modules.accounts.models import User
from app.modules.ai_quality.models import NLQuery, TrainingExample
from app.modules.ai_quality.schemas import (
    ChatMetrics,
    FixOut,
    FixPreviewHotel,
    MetricsOut,
    NLQueryOut,
    ScanMetrics,
    SearchMetrics,
    TrainingExampleOut,
    TrainingMetrics,
)
from app.modules.ai_quality.service import cards_for_ids, hotel_ids_in_order, run_readonly
from app.modules.chat.models import ChatMessage, TripChange
from app.modules.hotels.schemas import FixSqlIn
from app.modules.places.models import PlaceImage, Scan

router = APIRouter(prefix="/admin/ai", tags=["A5 · Admin AI quality"])
admin = require_role("admin")


def count(db: Session, stmt) -> int:
    return int(db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)


def ratio(part: int, whole: int) -> float | None:
    return round(part / whole, 3) if whole else None


@router.get("/metrics", response_model=MetricsOut)
def ai_metrics(user: User = Depends(admin), db: Session = Depends(get_db)) -> MetricsOut:
    """Why: the team needs to prove the AI works, for the admin dashboard and the graduation report.
    search: how many plain-language searches worked, failed or found nothing, and how fast.
    scans: recognized vs not sure, and how many the admin has labeled or still has to review.
    chat: how many suggested changes travelers kept. training: examples and photos the models learn from."""
    return build_metrics(db)


def build_metrics(db: Session) -> MetricsOut:
    """Shared with GET /admin/stats."""
    by_status = dict(db.execute(select(NLQuery.status, func.count()).group_by(NLQuery.status)).all())
    total = sum(by_status.values())
    latencies = sorted(db.scalars(select(NLQuery.latency_ms).where(NLQuery.latency_ms.is_not(None))))
    week_ago = datetime.now(UTC) - timedelta(days=7)
    search = SearchMetrics(
        total=total,
        ok=by_status.get("ok", 0),
        flagged=by_status.get("flagged", 0),
        failed=by_status.get("failed", 0),
        success_rate=ratio(by_status.get("ok", 0), total),
        avg_latency_ms=round(sum(latencies) / len(latencies), 1) if latencies else None,
        p95_latency_ms=latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else None,
        last_7_days=count(db, select(NLQuery.id).where(NLQuery.created_at >= week_ago)),
        fixed_by_admin=count(db, select(NLQuery.id).where(NLQuery.fixed_sql.is_not(None))),
    )

    threshold = settings.scan_confidence_threshold
    unsure = Scan.confidence < threshold
    scans = ScanMetrics(
        total=count(db, select(Scan.id)),
        recognized=count(db, select(Scan.id).where(Scan.confidence >= threshold, Scan.place_id.is_not(None))),
        not_sure=count(db, select(Scan.id).where(unsure)),
        labeled_by_admin=count(db, select(Scan.id).where(unsure, Scan.place_id.is_not(None))),
        waiting_review=count(db, select(Scan.id).where(unsure, Scan.place_id.is_(None))),
        avg_confidence=round(float(c), 3) if (c := db.scalar(select(func.avg(Scan.confidence)))) is not None else None,
        threshold=threshold,
    )

    changes = dict(db.execute(select(TripChange.status, func.count()).group_by(TripChange.status)).all())
    kept, undone = changes.get("kept", 0), changes.get("undone", 0)
    chat = ChatMetrics(
        messages=count(db, select(ChatMessage.id)),
        changes_proposed=sum(changes.values()),
        kept=kept,
        undone=undone,
        keep_rate=ratio(kept, kept + undone),
    )

    training = TrainingMetrics(
        nl2sql_examples=count(db, select(TrainingExample.id)),
        place_images=count(db, select(PlaceImage.id).where(PlaceImage.used_for_training.is_(True))),
        images_from_scans=count(db, select(PlaceImage.id).where(PlaceImage.source == "user_scan")),
    )
    return MetricsOut(search=search, scans=scans, chat=chat, training=training)


def to_query_out(db: Session, q: NLQuery) -> NLQueryOut:
    out = NLQueryOut.model_validate(q)
    out.in_training = db.scalar(select(TrainingExample.id).where(TrainingExample.source_query_id == q.id)) is not None
    return out


def get_query_or_404(db: Session, query_id: int) -> NLQuery:
    q = db.get(NLQuery, query_id)
    if q is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Query {query_id} not found")
    return q


@router.get("/queries", response_model=Page[NLQueryOut])
def list_queries(
    status_filter: str = Query(
        "failed",
        alias="status",
        pattern="^(failed|flagged|ok|all)$",
        description="failed = error, flagged = no results, ok = worked, all = everything",
    ),
    params: PageParams = Depends(),
    user: User = Depends(admin),
    db: Session = Depends(get_db),
) -> Page[NLQueryOut]:
    """Why: the admin reviews questions the search got wrong, newest first.
    Then: write the right SQL in POST /admin/ai/queries/{id}/fix."""
    stmt = select(NLQuery).order_by(NLQuery.created_at.desc(), NLQuery.id.desc())
    if status_filter != "all":
        stmt = stmt.where(NLQuery.status == status_filter)
    rows, total = paginate(db, stmt, params)
    return Page(data=[to_query_out(db, q) for q in rows], page=params.page, limit=params.limit, total=total)


@router.post("/queries/{query_id}/fix", response_model=FixOut)
def fix_query(query_id: int, body: FixSqlIn, user: User = Depends(admin), db: Session = Depends(get_db)) -> FixOut:
    """Why: the admin writes the correct SQL and tests it.
    It goes through the same checks as the AI (SELECT only, hotel_best_price and offers only, read-only,
    must return hotel_id). 400 with the reason when it fails; otherwise it's saved as fixed_sql and
    you get a preview of the hotels it returns.
    Then: POST /admin/ai/queries/{id}/add-to-training."""
    q = get_query_or_404(db, query_id)
    try:
        rows = run_readonly(body.sql)
    except Exception as exc:  # noqa: BLE001 - show the admin why the SQL can't be used
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{type(exc).__name__}: {exc}"[:500]) from exc
    cards = cards_for_ids(db, hotel_ids_in_order(rows))
    q.fixed_sql = body.sql.strip().rstrip(";").strip()
    q.reviewed_by = user.id
    db.commit()
    return FixOut(
        query=to_query_out(db, q),
        result_count=len(cards),
        preview=[FixPreviewHotel(hotel_id=c.id, hotel_name=c.name) for c in cards[:5]],
    )


@router.post("/queries/{query_id}/add-to-training", status_code=201, response_model=TrainingExampleOut)
def add_to_training(query_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> TrainingExampleOut:
    """Why: a fixed mistake should never happen again.
    The question + fixed SQL become a training example sent with every nl2sql call.
    409 when the query has no fixed SQL yet, or is already a training example."""
    q = get_query_or_404(db, query_id)
    if not q.fixed_sql:
        raise HTTPException(status.HTTP_409_CONFLICT, "Fix the SQL first (POST /admin/ai/queries/{id}/fix)")
    if db.scalar(select(TrainingExample.id).where(TrainingExample.source_query_id == q.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "This query is already a training example")
    example = TrainingExample(question=q.question, sql=q.fixed_sql, source_query_id=q.id, added_by=user.id)
    db.add(example)
    db.commit()
    db.refresh(example)
    return TrainingExampleOut.model_validate(example)


@router.get("/training-examples", response_model=list[TrainingExampleOut])
def list_training_examples(user: User = Depends(admin), db: Session = Depends(get_db)) -> list[TrainingExample]:
    """Why: see what the model is learning from, newest first."""
    return list(db.scalars(select(TrainingExample).order_by(TrainingExample.id.desc())))


@router.delete("/training-examples/{example_id}", status_code=204)
def delete_training_example(example_id: int, user: User = Depends(admin), db: Session = Depends(get_db)) -> Response:
    """Why: remove a wrong or outdated example so it stops misleading nl2sql."""
    example = db.get(TrainingExample, example_id)
    if example is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Training example {example_id} not found")
    db.delete(example)
    db.commit()
    return Response(status_code=204)
