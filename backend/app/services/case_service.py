"""Case CRUD, nested child management and automatic diary entries."""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case, CaseSection, DiaryEntry, Person, SeizedItem, User
from app.schemas.case import (
    CaseCreate,
    CaseSectionCreate,
    CaseUpdate,
    DiaryEntryCreate,
    PersonCreate,
    PersonUpdate,
    SeizedItemCreate,
    SeizedItemUpdate,
)
from app.services.nlp_service import infer_crime_type
from app.services.translation_service import translate

# Status transition → auto diary entry type
_STATUS_DIARY_TYPES = {
    "ARRESTED": "ARREST_MADE",
    "CHARGESHEETED": "CHARGESHEET_FILED",
    "CLOSED": "CASE_CLOSED",
}


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
async def create_case(db: AsyncSession, data: CaseCreate, current_user: User) -> Case:
    """Create a case with nested persons/items/sections and a FIR diary entry.

    Non-English narratives are translated to English and the crime type is
    inferred from the English text.
    """
    if data.language != "en":
        narrative_en, _ = await translate(data.narrative, data.language, "en")
    else:
        narrative_en = data.narrative

    crime_type = infer_crime_type(narrative_en)

    case = Case(
        fir_number=data.fir_number,
        station=data.station,
        ps_name=data.ps_name,
        incident_date=data.incident_date,
        incident_time=data.incident_time,
        incident_place=data.incident_place,
        crime_type=crime_type,
        narrative=data.narrative,
        narrative_en=narrative_en,
        language=data.language,
        io_id=current_user.id,
        persons=[Person(**p.model_dump()) for p in data.persons],
        items=[SeizedItem(**i.model_dump()) for i in data.items],
        sections=[CaseSection(**s.model_dump()) for s in data.sections],
    )
    case.diary_entries.append(
        DiaryEntry(
            entry_type="FIR_FILED",
            description=(
                f"FIR {data.fir_number} filed at {data.station} police station."
            ),
            officer_id=current_user.id,
        )
    )
    db.add(case)
    await db.commit()
    return await get_case(db, case.id)


async def get_case(db: AsyncSession, case_id: str) -> Case:
    """Fetch a case by id with relationships loaded. 404 if missing/deleted."""
    case = await db.scalar(
        select(Case).where(Case.id == case_id, Case.is_deleted.is_(False))
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


async def list_cases(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    io_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[int, list[Case]]:
    """List non-deleted cases with filters, newest first. Returns (total, page)."""
    filters = [Case.is_deleted.is_(False)]
    if status:
        filters.append(Case.status == status)
    if io_id:
        filters.append(Case.io_id == io_id)
    if date_from:
        filters.append(Case.incident_date >= date_from)
    if date_to:
        filters.append(Case.incident_date <= date_to)

    total = await db.scalar(
        select(func.count()).select_from(Case).where(*filters)
    ) or 0

    result = await db.scalars(
        select(Case)
        .where(*filters)
        .order_by(Case.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return total, list(result.all())


async def update_case(
    db: AsyncSession, case_id: str, data: CaseUpdate, current_user: User
) -> Case:
    """Apply partial updates; re-run NLP on narrative change, auto-diary on status change."""
    case = await get_case(db, case_id)
    fields = data.model_dump(exclude_unset=True)

    old_status = case.status
    for key, value in fields.items():
        setattr(case, key, value)

    if "narrative" in fields:
        if case.language != "en":
            narrative_en, _ = await translate(case.narrative, case.language, "en")
        else:
            narrative_en = case.narrative
        case.narrative_en = narrative_en
        # Only overwrite crime_type when the officer didn't set it explicitly
        if "crime_type" not in fields:
            case.crime_type = infer_crime_type(narrative_en)

    new_status = fields.get("status")
    if new_status and new_status != old_status and new_status in _STATUS_DIARY_TYPES:
        db.add(
            DiaryEntry(
                case_id=case.id,
                entry_type=_STATUS_DIARY_TYPES[new_status],
                description=f"Case status changed from {old_status} to {new_status}.",
                officer_id=current_user.id,
            )
        )

    await db.commit()
    return await get_case(db, case_id)


async def soft_delete_case(db: AsyncSession, case_id: str, current_user: User) -> None:
    """Soft-delete a case and record a CASE_DELETED diary entry."""
    case = await get_case(db, case_id)
    case.is_deleted = True
    db.add(
        DiaryEntry(
            case_id=case.id,
            entry_type="CASE_DELETED",
            description=f"Case with FIR {case.fir_number} was deleted.",
            officer_id=current_user.id,
        )
    )
    await db.commit()


async def search_cases(db: AsyncSession, q: str, limit: int = 50) -> list[Case]:
    """Case-insensitive keyword search across the main text fields."""
    pattern = f"%{q}%"
    result = await db.scalars(
        select(Case)
        .where(
            Case.is_deleted.is_(False),
            or_(
                Case.fir_number.ilike(pattern),
                Case.narrative.ilike(pattern),
                Case.narrative_en.ilike(pattern),
                Case.incident_place.ilike(pattern),
                Case.crime_type.ilike(pattern),
                Case.station.ilike(pattern),
            ),
        )
        .order_by(Case.created_at.desc())
        .limit(limit)
    )
    return list(result.all())


# ---------------------------------------------------------------------------
# Persons
# ---------------------------------------------------------------------------
async def add_person(db: AsyncSession, case_id: str, data: PersonCreate) -> Person:
    """Add a victim/accused/witness to a case."""
    await get_case(db, case_id)
    person = Person(case_id=case_id, **data.model_dump())
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person


async def _get_person(db: AsyncSession, case_id: str, person_id: str) -> Person:
    person = await db.scalar(
        select(Person).where(Person.id == person_id, Person.case_id == case_id)
    )
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


async def update_person(
    db: AsyncSession, case_id: str, person_id: str, data: PersonUpdate
) -> Person:
    """Partially update a person on a case. 404 if not found on that case."""
    await get_case(db, case_id)
    person = await _get_person(db, case_id, person_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(person, key, value)
    await db.commit()
    await db.refresh(person)
    return person


async def delete_person(db: AsyncSession, case_id: str, person_id: str) -> None:
    """Remove a person from a case. 404 if not found on that case."""
    await get_case(db, case_id)
    person = await _get_person(db, case_id, person_id)
    await db.delete(person)
    await db.commit()


# ---------------------------------------------------------------------------
# Seized items
# ---------------------------------------------------------------------------
async def add_item(db: AsyncSession, case_id: str, data: SeizedItemCreate) -> SeizedItem:
    """Add a seized item and record an EVIDENCE_SEIZED diary entry."""
    await get_case(db, case_id)
    item = SeizedItem(case_id=case_id, **data.model_dump())
    db.add(item)
    db.add(
        DiaryEntry(
            case_id=case_id,
            entry_type="EVIDENCE_SEIZED",
            description=f"Evidence seized: {data.item_name}.",
            officer_id=None,
        )
    )
    await db.commit()
    await db.refresh(item)
    return item


async def _get_item(db: AsyncSession, case_id: str, item_id: str) -> SeizedItem:
    item = await db.scalar(
        select(SeizedItem).where(
            SeizedItem.id == item_id, SeizedItem.case_id == case_id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Seized item not found")
    return item


async def update_item(
    db: AsyncSession, case_id: str, item_id: str, data: SeizedItemUpdate
) -> SeizedItem:
    """Partially update a seized item. 404 if not found on that case."""
    await get_case(db, case_id)
    item = await _get_item(db, case_id, item_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, case_id: str, item_id: str) -> None:
    """Remove a seized item from a case. 404 if not found on that case."""
    await get_case(db, case_id)
    item = await _get_item(db, case_id, item_id)
    await db.delete(item)
    await db.commit()


# ---------------------------------------------------------------------------
# Legal sections
# ---------------------------------------------------------------------------
async def add_section(
    db: AsyncSession, case_id: str, data: CaseSectionCreate
) -> CaseSection:
    """Apply a legal section to a case."""
    await get_case(db, case_id)
    section = CaseSection(case_id=case_id, **data.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


async def delete_section(db: AsyncSession, case_id: str, section_id: str) -> None:
    """Remove an applied legal section. 404 if not found on that case."""
    await get_case(db, case_id)
    section = await db.scalar(
        select(CaseSection).where(
            CaseSection.id == section_id, CaseSection.case_id == case_id
        )
    )
    if section is None:
        raise HTTPException(status_code=404, detail="Case section not found")
    await db.delete(section)
    await db.commit()


# ---------------------------------------------------------------------------
# Diary
# ---------------------------------------------------------------------------
async def add_diary_entry(
    db: AsyncSession, case_id: str, entry: DiaryEntryCreate, officer_id: str | None
) -> DiaryEntry:
    """Add a manual diary entry to a case."""
    await get_case(db, case_id)
    diary_entry = DiaryEntry(
        case_id=case_id,
        entry_type=entry.entry_type,
        description=entry.description,
        officer_id=officer_id,
    )
    db.add(diary_entry)
    await db.commit()
    await db.refresh(diary_entry)
    return diary_entry
