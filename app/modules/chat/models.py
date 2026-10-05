"""Tables: chat_messages, trip_changes. Owner: Person 3."""

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, IdMixin

MESSAGE_ROLES = ("user", "assistant")
CHANGE_STATUSES = ("proposed", "kept", "undone")


class ChatMessage(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "chat_messages"

    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(Enum(*MESSAGE_ROLES, name="message_role"))
    content: Mapped[str] = mapped_column(Text)


class TripChange(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "trip_changes"

    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"))
    summary: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    cost_delta: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # {"before": {...}, "after": {...}} so Undo can restore the trip exactly.
    diff: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        Enum(*CHANGE_STATUSES, name="change_status"), default="proposed", server_default="proposed"
    )
