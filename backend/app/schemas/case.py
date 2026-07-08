from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserOut


# ---------- Persons ----------
class PersonBase(BaseModel):
    role: str = Field(pattern="^(VICTIM|ACCUSED|WITNESS)$")
    name: str
    age: int | None = None
    gender: str | None = None
    address: str | None = None
    phone: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    notes: str | None = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(VICTIM|ACCUSED|WITNESS)$")
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    address: str | None = None
    phone: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    notes: str | None = None


class PersonOut(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    created_at: datetime


# ---------- Seized items ----------
class SeizedItemBase(BaseModel):
    item_name: str
    quantity: str | None = None
    description: str | None = None
    seized_from: str | None = None
    seized_at: datetime | None = None


class SeizedItemCreate(SeizedItemBase):
    pass


class SeizedItemUpdate(BaseModel):
    item_name: str | None = None
    quantity: str | None = None
    description: str | None = None
    seized_from: str | None = None
    seized_at: datetime | None = None


class SeizedItemOut(SeizedItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    created_at: datetime


# ---------- Case sections ----------
class CaseSectionCreate(BaseModel):
    act: str = Field(pattern="^(BNS|BNSS|BSA|IPC|CrPC)$")
    section: str
    description: str | None = None
    source: str = Field(default="OFFICER_ADDED", pattern="^(AI_SUGGESTED|OFFICER_ADDED)$")
    confidence: float | None = None


class CaseSectionOut(CaseSectionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    created_at: datetime


# ---------- Diary ----------
class DiaryEntryCreate(BaseModel):
    entry_type: str | None = None
    description: str


class DiaryEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    entry_type: str | None = None
    description: str
    officer: UserOut | None = None
    entry_date: datetime


# ---------- Cases ----------
class CaseCreate(BaseModel):
    fir_number: str
    station: str
    ps_name: str | None = None
    incident_date: date
    incident_time: time | None = None
    incident_place: str | None = None
    narrative: str
    language: str = Field(default="en", pattern="^(gu|hi|en)$")
    persons: list[PersonCreate] = []
    items: list[SeizedItemCreate] = []
    sections: list[CaseSectionCreate] = []


class CaseUpdate(BaseModel):
    station: str | None = None
    ps_name: str | None = None
    incident_date: date | None = None
    incident_time: time | None = None
    incident_place: str | None = None
    narrative: str | None = None
    crime_type: str | None = None
    status: str | None = Field(
        default=None, pattern="^(OPEN|ARRESTED|CHARGESHEETED|CLOSED)$"
    )


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fir_number: str
    station: str
    incident_date: date
    crime_type: str | None = None
    status: str
    created_at: datetime
    io: UserOut | None = None


class CaseOut(CaseListItem):
    ps_name: str | None = None
    incident_time: time | None = None
    incident_place: str | None = None
    narrative: str
    narrative_en: str | None = None
    language: str
    updated_at: datetime
    persons: list[PersonOut] = []
    items: list[SeizedItemOut] = []
    sections: list[CaseSectionOut] = []
    diary_entries: list[DiaryEntryOut] = []


class PaginatedCases(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[CaseListItem]
