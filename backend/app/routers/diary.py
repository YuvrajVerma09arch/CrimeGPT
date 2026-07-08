"""Case diary endpoints — timestamped FIR-to-arrest investigation timeline."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.case import DiaryEntryCreate, DiaryEntryOut
from app.services import case_service
from app.utils.security import get_current_user

router = APIRouter(tags=["diary"], dependencies=[Depends(get_current_user)])


@router.get("/cases/{case_id}/diary", response_model=list[DiaryEntryOut])
async def list_diary_entries(
    case_id: str, db: AsyncSession = Depends(get_db)
) -> list[DiaryEntryOut]:
    """Full diary timeline for a case."""
    case = await case_service.get_case(db, case_id)
    return [DiaryEntryOut.model_validate(e) for e in case.diary_entries]


@router.post("/cases/{case_id}/diary", response_model=DiaryEntryOut)
async def add_diary_entry(
    case_id: str,
    entry: DiaryEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiaryEntryOut:
    """Append a diary entry to a case, attributed to the current officer."""
    created = await case_service.add_diary_entry(
        db, case_id, entry, officer_id=current_user.id
    )
    return DiaryEntryOut.model_validate(created)
