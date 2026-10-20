"""Response shapes for the admin AI-quality screen. Owner: Person 5."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NLQueryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    question: str
    generated_sql: str | None
    status: str  # ok | flagged (no results) | failed (error)
    error: str | None
    result_count: int | None
    latency_ms: int | None
    fixed_sql: str | None
    reviewed_by: int | None
    in_training: bool = False
    created_at: datetime


class FixPreviewHotel(BaseModel):
    hotel_id: int
    hotel_name: str


class FixOut(BaseModel):
    query: NLQueryOut
    result_count: int
    preview: list[FixPreviewHotel]  # first hotels the fixed SQL returns


class TrainingExampleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    sql: str
    source_query_id: int | None
    added_by: int | None
    created_at: datetime


class SearchMetrics(BaseModel):
    total: int
    ok: int
    flagged: int
    failed: int
    success_rate: float | None  # ok / total
    avg_latency_ms: float | None
    p95_latency_ms: int | None
    last_7_days: int
    fixed_by_admin: int


class ScanMetrics(BaseModel):
    total: int
    recognized: int
    not_sure: int
    labeled_by_admin: int
    waiting_review: int
    avg_confidence: float | None
    threshold: float


class ChatMetrics(BaseModel):
    messages: int
    changes_proposed: int
    kept: int
    undone: int
    keep_rate: float | None  # kept / changes that got a decision


class TrainingMetrics(BaseModel):
    nl2sql_examples: int
    place_images: int
    images_from_scans: int


class MetricsOut(BaseModel):
    search: SearchMetrics
    scans: ScanMetrics
    chat: ChatMetrics
    training: TrainingMetrics
