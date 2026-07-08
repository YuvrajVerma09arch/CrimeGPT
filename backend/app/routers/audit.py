"""Audit trail query endpoint — immutable change history across audited tables."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.audit import AuditLogOut
from app.services import audit_service
from app.utils.security import get_current_user

router = APIRouter(tags=["audit"], dependencies=[Depends(get_current_user)])


@router.get("/audit", response_model=list[AuditLogOut])
async def query_audit_logs(
    case_id: str | None = None,
    user_id: str | None = None,
    table_name: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogOut]:
    """Query audit logs filtered by case, officer, table or date range."""
    logs = await audit_service.query_logs(
        db,
        case_id=case_id,
        user_id=user_id,
        table_name=table_name,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return [AuditLogOut.model_validate(log) for log in logs]
