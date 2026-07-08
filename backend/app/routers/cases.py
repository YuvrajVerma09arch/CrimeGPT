"""Case CRUD, full-text search, and person/item/section sub-resources."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.case import (
    CaseCreate,
    CaseListItem,
    CaseOut,
    CaseSectionCreate,
    CaseSectionOut,
    CaseUpdate,
    PaginatedCases,
    PersonCreate,
    PersonOut,
    PersonUpdate,
    SeizedItemCreate,
    SeizedItemOut,
    SeizedItemUpdate,
)
from app.services import case_service
from app.utils.security import get_current_user, require_role

router = APIRouter(
    prefix="/cases",
    tags=["cases"],
    dependencies=[Depends(get_current_user)],
)


# ---------- Cases ----------
@router.get("", response_model=PaginatedCases)
async def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None, pattern="^(OPEN|ARRESTED|CHARGESHEETED|CLOSED)$"),
    io_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedCases:
    """Paginated case list with optional status / officer / date filters."""
    total, cases = await case_service.list_cases(
        db,
        page=page,
        page_size=page_size,
        status=status,
        io_id=io_id,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedCases(
        total=total,
        page=page,
        page_size=page_size,
        items=[CaseListItem.model_validate(c) for c in cases],
    )


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseOut:
    """Register a new FIR / case with nested persons, items and sections."""
    case = await case_service.create_case(db, data, current_user)
    return CaseOut.model_validate(case)


# NOTE: /search MUST be declared before /{case_id} so it is not captured as an id.
@router.get("/search", response_model=list[CaseListItem])
async def search_cases(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[CaseListItem]:
    """Keyword search across FIR number, narrative and place."""
    cases = await case_service.search_cases(db, q, limit=limit)
    return [CaseListItem.model_validate(c) for c in cases]


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)) -> CaseOut:
    """Full case detail including persons, items, sections and diary."""
    case = await case_service.get_case(db, case_id)
    return CaseOut.model_validate(case)


@router.put("/{case_id}", response_model=CaseOut)
async def update_case(
    case_id: str,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseOut:
    """Update editable case fields (change is captured by the audit trail)."""
    case = await case_service.update_case(db, case_id, data, current_user)
    return CaseOut.model_validate(case)


@router.delete("/{case_id}", status_code=204)
async def delete_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("SHO", "LEGAL_ADVISOR")),
) -> None:
    """Soft-delete a case. Restricted to SHO / LEGAL_ADVISOR."""
    await case_service.soft_delete_case(db, case_id, current_user)


# ---------- Persons ----------
@router.post("/{case_id}/persons", response_model=PersonOut)
async def add_person(
    case_id: str, data: PersonCreate, db: AsyncSession = Depends(get_db)
) -> PersonOut:
    """Attach a victim / accused / witness to a case."""
    person = await case_service.add_person(db, case_id, data)
    return PersonOut.model_validate(person)


@router.put("/{case_id}/persons/{person_id}", response_model=PersonOut)
async def update_person(
    case_id: str, person_id: str, data: PersonUpdate, db: AsyncSession = Depends(get_db)
) -> PersonOut:
    """Update a person on a case."""
    person = await case_service.update_person(db, case_id, person_id, data)
    return PersonOut.model_validate(person)


@router.delete("/{case_id}/persons/{person_id}", status_code=204)
async def delete_person(
    case_id: str, person_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    """Remove a person from a case."""
    await case_service.delete_person(db, case_id, person_id)


# ---------- Seized items ----------
@router.post("/{case_id}/items", response_model=SeizedItemOut)
async def add_item(
    case_id: str, data: SeizedItemCreate, db: AsyncSession = Depends(get_db)
) -> SeizedItemOut:
    """Record a seized item against a case."""
    item = await case_service.add_item(db, case_id, data)
    return SeizedItemOut.model_validate(item)


@router.put("/{case_id}/items/{item_id}", response_model=SeizedItemOut)
async def update_item(
    case_id: str, item_id: str, data: SeizedItemUpdate, db: AsyncSession = Depends(get_db)
) -> SeizedItemOut:
    """Update a seized item."""
    item = await case_service.update_item(db, case_id, item_id, data)
    return SeizedItemOut.model_validate(item)


@router.delete("/{case_id}/items/{item_id}", status_code=204)
async def delete_item(
    case_id: str, item_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    """Remove a seized item from a case."""
    await case_service.delete_item(db, case_id, item_id)


# ---------- Legal sections ----------
@router.post("/{case_id}/sections", response_model=CaseSectionOut)
async def add_section(
    case_id: str, data: CaseSectionCreate, db: AsyncSession = Depends(get_db)
) -> CaseSectionOut:
    """Apply a legal section (AI-suggested or officer-added) to a case."""
    section = await case_service.add_section(db, case_id, data)
    return CaseSectionOut.model_validate(section)


@router.delete("/{case_id}/sections/{section_id}", status_code=204)
async def delete_section(
    case_id: str, section_id: str, db: AsyncSession = Depends(get_db)
) -> None:
    """Remove an applied legal section from a case."""
    await case_service.delete_section(db, case_id, section_id)
