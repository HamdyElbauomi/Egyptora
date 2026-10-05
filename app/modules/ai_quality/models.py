"""Tables: nl_queries, training_examples. Owner: Person 5."""

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

QUERY_STATUSES = ("ok", "failed", "flagged")


class NLQuery(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "nl_queries"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    question: Mapped[str] = mapped_column(Text)
    generated_sql: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Enum(*QUERY_STATUSES, name="nl_query_status"), default="ok")
    error: Mapped[str | None] = mapped_column(Text)
    result_count: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    fixed_sql: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))


class TrainingExample(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "training_examples"

    question: Mapped[str] = mapped_column(Text)
    sql: Mapped[str] = mapped_column(Text)
    source_query_id: Mapped[int | None] = mapped_column(ForeignKey("nl_queries.id", ondelete="SET NULL"))
    added_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
