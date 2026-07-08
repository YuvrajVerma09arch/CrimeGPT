import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    fir_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    station: Mapped[str] = mapped_column(String(255), nullable=False)
    ps_name: Mapped[str | None] = mapped_column(String(255))
    incident_date: Mapped[date] = mapped_column(Date, nullable=False)
    incident_time: Mapped[time | None] = mapped_column(Time)
    incident_place: Mapped[str | None] = mapped_column(Text)
    crime_type: Mapped[str | None] = mapped_column(String(100))  # extracted by NLP
    narrative: Mapped[str] = mapped_column(Text, nullable=False)  # original officer input
    narrative_en: Mapped[str | None] = mapped_column(Text)  # English translation
    language: Mapped[str] = mapped_column(String(5), default="en")  # gu | hi | en
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    io_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    io = relationship("User", lazy="selectin")
    persons: Mapped[list["Person"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    items: Mapped[list["SeizedItem"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    sections: Mapped[list["CaseSection"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )
    diary_entries: Mapped[list["DiaryEntry"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", lazy="selectin",
        order_by="DiaryEntry.entry_date",
    )
    documents = relationship(
        "Document", back_populates="case", cascade="all, delete-orphan", lazy="selectin"
    )


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # VICTIM | ACCUSED | WITNESS
    name: Mapped[str] = mapped_column(Text, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(10))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(20))
    id_type: Mapped[str | None] = mapped_column(String(50))  # Aadhaar / PAN / Passport
    id_number: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="persons")


class SeizedItem(Base):
    __tablename__ = "seized_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    seized_from: Mapped[str | None] = mapped_column(Text)
    seized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="items")


class CaseSection(Base):
    __tablename__ = "case_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"))
    act: Mapped[str] = mapped_column(String(20), nullable=False)  # BNS | BNSS | BSA | IPC | CrPC
    section: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(20))  # AI_SUGGESTED | OFFICER_ADDED
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="sections")


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"))
    entry_type: Mapped[str | None] = mapped_column(String(50))  # FIR_FILED / EVIDENCE_SEIZED / ...
    description: Mapped[str] = mapped_column(Text, nullable=False)
    officer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship(back_populates="diary_entries")
    officer = relationship("User", lazy="selectin")
