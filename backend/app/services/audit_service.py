"""Read-side queries over the immutable audit log."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, CaseSection, Document, Person, SeizedItem


async def query_logs(
    db: AsyncSession,
    case_id: str | None = None,
    user_id: str | None = None,
    table_name: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 200,
) -> list[AuditLog]:
    """Query audit log rows, newest first.

    ``case_id`` matches the case row itself plus every child record
    (persons, seized items, case sections, documents) of that case.
    """
    stmt = select(AuditLog)

    if case_id:
        person_ids = (
            await db.scalars(select(Person.id).where(Person.case_id == case_id))
        ).all()
        item_ids = (
            await db.scalars(select(SeizedItem.id).where(SeizedItem.case_id == case_id))
        ).all()
        section_ids = (
            await db.scalars(select(CaseSection.id).where(CaseSection.case_id == case_id))
        ).all()
        document_ids = (
            await db.scalars(select(Document.id).where(Document.case_id == case_id))
        ).all()
        record_ids = [case_id, *person_ids, *item_ids, *section_ids, *document_ids]
        stmt = stmt.where(AuditLog.record_id.in_(record_ids))

    if user_id:
        stmt = stmt.where(AuditLog.changed_by == user_id)
    if table_name:
        stmt = stmt.where(AuditLog.table_name == table_name)
    if date_from:
        stmt = stmt.where(AuditLog.changed_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.changed_at <= date_to)

    stmt = stmt.order_by(AuditLog.changed_at.desc()).limit(limit)
    result = await db.scalars(stmt)
    return list(result.all())
