import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """Immutable change log — rows are only ever inserted, never mutated."""

    __tablename__ = "audit_logs"
    __table_args__ = (Index("idx_audit_record", "table_name", "record_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    table_name: Mapped[str | None] = mapped_column(String(100))
    record_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str | None] = mapped_column(String(20))  # INSERT | UPDATE | DELETE
    old_data: Mapped[dict | None] = mapped_column(JSON)
    new_data: Mapped[dict | None] = mapped_column(JSON)
    changed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user = relationship("User", lazy="selectin")
