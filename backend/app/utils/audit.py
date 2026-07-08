"""Automatic audit trail via SQLAlchemy event listeners.

Every INSERT/UPDATE/DELETE on the audited tables is written to `audit_logs`
inside the same flush — no manual service calls needed. The acting user is
picked up from `current_user_id_ctx` (set by the auth dependency).
"""
import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.utils.security import current_user_id_ctx

AUDITED_TABLES = {"cases", "persons", "seized_items", "case_sections", "documents"}

# Never log password-like or oversized fields
EXCLUDED_FIELDS = {"password"}


def _jsonable(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _snapshot(obj) -> dict:
    """Current column values of an ORM object as a JSON-safe dict."""
    return {
        c.key: _jsonable(getattr(obj, c.key))
        for c in inspect(obj).mapper.column_attrs
        if c.key not in EXCLUDED_FIELDS
    }


def _changed(obj) -> tuple[dict, dict]:
    """(old, new) dicts containing only the attributes modified this flush."""
    old, new = {}, {}
    state = inspect(obj)
    for attr in state.mapper.column_attrs:
        if attr.key in EXCLUDED_FIELDS:
            continue
        hist = state.attrs[attr.key].history
        if hist.has_changes():
            old[attr.key] = _jsonable(hist.deleted[0]) if hist.deleted else None
            new[attr.key] = _jsonable(hist.added[0]) if hist.added else None
    return old, new


def _audit_row(table_name: str, record_id, action: str, old_data, new_data) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "table_name": table_name,
        "record_id": str(record_id) if record_id is not None else None,
        "action": action,
        "old_data": old_data,
        "new_data": new_data,
        "changed_by": current_user_id_ctx.get(),
        "changed_at": datetime.now(timezone.utc),
    }


@event.listens_for(Session, "after_flush")
def log_changes(session: Session, flush_context) -> None:
    rows: list[dict] = []

    for obj in session.new:
        if obj.__tablename__ in AUDITED_TABLES:
            rows.append(_audit_row(obj.__tablename__, obj.id, "INSERT", None, _snapshot(obj)))

    for obj in session.dirty:
        if obj.__tablename__ in AUDITED_TABLES and session.is_modified(obj):
            old, new = _changed(obj)
            if new:
                rows.append(_audit_row(obj.__tablename__, obj.id, "UPDATE", old, new))

    for obj in session.deleted:
        if obj.__tablename__ in AUDITED_TABLES:
            rows.append(_audit_row(obj.__tablename__, obj.id, "DELETE", _snapshot(obj), None))

    if rows:
        # Core insert on the flush connection — safe inside after_flush
        # (adding ORM objects here would recurse into another flush).
        session.connection().execute(AuditLog.__table__.insert(), rows)
