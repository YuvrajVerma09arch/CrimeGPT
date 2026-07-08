"""Seed demo users and sample cases for the hackathon demo.

Run from ``backend/`` with::

    python -m app.seeds.demo_data

Idempotent: existing users (by badge_no) are skipped, and sample cases are
only created when the cases table is empty. Cases are created THROUGH
``case_service.create_case`` so the NLP crime-type inference, FIR diary
entries and audit trail all fire exactly as they would in production.
"""
import asyncio
import json
from datetime import date, time
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Importing registers the SQLAlchemy after_flush audit listeners so that
# seeded rows show up in the audit trail too.
import app.utils.audit  # noqa: F401
from app.database import async_session_maker, engine, init_db
from app.models import Case, User
from app.schemas.case import (
    CaseCreate,
    CaseSectionCreate,
    PersonCreate,
    SeizedItemCreate,
)
from app.services import case_service
from app.services.nlp_service import infer_crime_type
from app.services.translation_service import detect_language
from app.utils.security import current_user_id_ctx, hash_password

SAMPLES_PATH = Path(__file__).resolve().parents[2] / "data" / "samples" / "sample_firs.json"

DEMO_PASSWORD = "demo123"

DEMO_USERS = [
    {
        "badge_no": "IO001",
        "name": "Insp. R. K. Patel",
        "role": "IO",
        "station": "Navrangpura Police Station",
    },
    {
        "badge_no": "SHO001",
        "name": "SHO M. D. Desai",
        "role": "SHO",
        "station": "Navrangpura Police Station",
    },
    {
        "badge_no": "LA001",
        "name": "Adv. S. Mehta",
        "role": "LEGAL_ADVISOR",
        "station": "Ahmedabad City",
    },
]

# Per-sample metadata, index-aligned with data/samples/sample_firs.json:
# [0] en chain/mobile snatching, [1] hi house burglary, [2] gu UPI fraud.
CASE_SPECS: list[dict] = [
    {
        "fir_number": "NVR/2026/0142",
        "station": "Navrangpura",
        "ps_name": "Navrangpura Police Station",
        "incident_date": date(2026, 7, 4),
        "incident_time": time(21, 30),
        "incident_place": "Near CG Road, Navrangpura, Ahmedabad",
        "persons": [
            PersonCreate(
                role="VICTIM",
                name="Smt. Kiran J. Shah",
                age=34,
                gender="F",
                address="B-204, Shantivan Apartments, Navrangpura, Ahmedabad",
                phone="9825012345",
            ),
            PersonCreate(
                role="ACCUSED",
                name="Raju Solanki",
                age=26,
                gender="M",
                address="Naroda, Ahmedabad",
                notes="Pillion rider on black motorcycle without number plate.",
            ),
        ],
        "items": [
            SeizedItemCreate(
                item_name="Iron rod",
                quantity="1",
                description="Weapon used to threaten the complainant; recovered near Stadium Circle.",
                seized_from="Scene of offence, Stadium Circle",
            ),
            SeizedItemCreate(
                item_name="Black motorcycle (no number plate)",
                quantity="1",
                description="Vehicle used by the accused during the snatching.",
                seized_from="Abandoned near Stadium Circle",
            ),
        ],
        "sections": [
            CaseSectionCreate(
                act="BNS", section="304", description="Snatching", source="OFFICER_ADDED"
            ),
            CaseSectionCreate(
                act="BNS",
                section="115",
                description="Voluntarily causing hurt",
                source="OFFICER_ADDED",
            ),
        ],
    },
    {
        "fir_number": "MNG/2026/0387",
        "station": "Maninagar",
        "ps_name": "Maninagar Police Station",
        "incident_date": date(2026, 7, 2),
        "incident_time": time(23, 0),
        "incident_place": "Maninagar, Ahmedabad",
        "persons": [
            PersonCreate(
                role="VICTIM",
                name="Shri Mahesh D. Patel",
                age=48,
                gender="M",
                address="12, Shreeji Society, Maninagar, Ahmedabad",
                phone="9898054321",
            ),
            PersonCreate(
                role="ACCUSED",
                name="Ramesh Thakor",
                age=31,
                gender="M",
                address="Isanpur, Ahmedabad",
                notes="Suspected on the basis of prior modus operandi; absconding.",
            ),
        ],
        "items": [],
        "sections": [
            CaseSectionCreate(
                act="BNS",
                section="305",
                description="Theft in a dwelling house",
                source="OFFICER_ADDED",
            ),
            CaseSectionCreate(
                act="BNS",
                section="329",
                description="Criminal trespass and house-trespass",
                source="OFFICER_ADDED",
            ),
        ],
    },
    {
        "fir_number": "CYB/2026/0056",
        "station": "Cyber Crime Cell, Ahmedabad",
        "ps_name": "Cyber Crime Police Station, Ahmedabad",
        "incident_date": date(2026, 7, 1),
        "incident_time": None,
        "incident_place": "Complainant's residence, Satellite, Ahmedabad",
        "persons": [
            PersonCreate(
                role="VICTIM",
                name="Shri Nilesh K. Trivedi",
                age=41,
                gender="M",
                address="C-9, Sarjan Tower, Satellite, Ahmedabad",
                phone="9724098765",
            ),
            PersonCreate(
                role="ACCUSED",
                name="Unknown caller (mobile 98XXXXXX21)",
                notes="Posed as a bank officer demanding KYC update; OTP obtained by deceit.",
            ),
        ],
        "items": [],
        "sections": [
            CaseSectionCreate(
                act="BNS", section="318", description="Cheating", source="OFFICER_ADDED"
            ),
            CaseSectionCreate(
                act="BNS",
                section="319",
                description="Cheating by personation",
                source="OFFICER_ADDED",
            ),
        ],
    },
]


async def seed_users(db: AsyncSession) -> dict[str, User]:
    """Create the three demo users; skip any badge_no that already exists."""
    users: dict[str, User] = {}
    for spec in DEMO_USERS:
        user = await db.scalar(select(User).where(User.badge_no == spec["badge_no"]))
        if user is not None:
            print(f"  - user {spec['badge_no']} already exists — skipped")
        else:
            user = User(
                name=spec["name"],
                badge_no=spec["badge_no"],
                role=spec["role"],
                station=spec["station"],
                password=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"  + created user {spec['badge_no']} ({spec['role']}: {spec['name']})")
        users[spec["badge_no"]] = user
    return users


async def seed_cases(db: AsyncSession, io_user: User) -> None:
    """Create the three demo cases from sample_firs.json, if no cases exist."""
    existing = await db.scalar(select(func.count()).select_from(Case)) or 0
    if existing > 0:
        print(f"  - {existing} case(s) already present — skipping sample cases")
        return

    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))

    # Attribute the seeded rows to the demo IO in the audit trail.
    current_user_id_ctx.set(io_user.id)

    for sample, spec in zip(samples, CASE_SPECS):
        data = CaseCreate(
            fir_number=spec["fir_number"],
            station=spec["station"],
            ps_name=spec["ps_name"],
            incident_date=spec["incident_date"],
            incident_time=spec["incident_time"],
            incident_place=spec["incident_place"],
            narrative=sample["narrative"],
            language=sample["language"],
            persons=spec["persons"],
            items=spec["items"],
            sections=spec["sections"],
        )
        case = await case_service.create_case(db, data, io_user)
        print(
            f"  + created case {case.fir_number} "
            f"(lang={case.language}, crime_type={case.crime_type})"
        )

        # If no translation engine was available (passthrough), narrative_en
        # still contains the original gu/hi text — patch it from the curated
        # English translation shipped with the sample and re-run NLP on it.
        if case.language != "en" and detect_language(case.narrative_en or "") != "en":
            case.narrative_en = sample["narrative_en"]
            case.crime_type = infer_crime_type(case.narrative_en)
            await db.commit()
            print(
                f"    ~ patched narrative_en from sample (translation passthrough); "
                f"crime_type={case.crime_type}"
            )


async def main() -> None:
    print("CrimeGPT demo seed")
    print("==================")
    await init_db()

    async with async_session_maker() as db:
        print("Users:")
        users = await seed_users(db)
        print("Cases:")
        await seed_cases(db, users["IO001"])

    await engine.dispose()
    print("Done. Demo credentials: IO001 / SHO001 / LA001, password 'demo123'.")


if __name__ == "__main__":
    asyncio.run(main())
