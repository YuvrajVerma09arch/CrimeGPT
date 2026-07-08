"""Shared pytest fixtures for the CrimeGPT backend test suite.

The test environment MUST be pinned before any ``app.*`` import — app.config
builds a cached module-level Settings singleton at import time.
"""
import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_crimegpt.db"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["CHROMA_DB_PATH"] = "./test_chroma"
os.environ["JWT_SECRET"] = "pytest-only-jwt-secret-not-for-production-32ch"
os.environ["USE_CELERY"] = "false"
os.environ["TRANSLATION_SERVICE_URL"] = ""
os.environ["GOOGLE_TRANSLATE_API_KEY"] = ""

import asyncio  # noqa: E402
import shutil  # noqa: E402
import uuid  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

# Importing registers the SQLAlchemy after_flush audit listeners — the ASGI
# transport does not run the FastAPI lifespan, so this must happen here.
import app.utils.audit  # noqa: F401, E402
from app.database import async_session_maker, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import document_service, legal_service  # noqa: E402
from app.utils.security import create_access_token, hash_password  # noqa: E402

TEST_DB_FILE = Path("test_crimegpt.db")

IRON_ROD_NARRATIVE = (
    "On 05/07/2026 at about 21:00 hours, the accused attacked the complainant "
    "near CG Road, Navrangpura, Ahmedabad with an iron rod and assaulted him, "
    "causing grievous hurt and a fracture of the left arm. The accused also "
    "snatched his mobile phone and threatened him with dire consequences "
    "before fleeing on a motorcycle."
)


@pytest.fixture(scope="session", autouse=True)
def _database():
    """Create the schema once per session; wipe all test artifacts afterwards.

    httpx's ASGITransport does not run the FastAPI lifespan, so the startup
    pieces (init_db, audit listener import, corpus load, docx templates) are
    executed directly here.
    """
    if TEST_DB_FILE.exists():
        TEST_DB_FILE.unlink()

    async def _setup() -> None:
        await init_db()
        await engine.dispose()  # do not leak connections bound to this loop

    asyncio.run(_setup())
    legal_service.load_corpus()
    document_service.ensure_templates()

    yield

    asyncio.run(engine.dispose())
    TEST_DB_FILE.unlink(missing_ok=True)
    shutil.rmtree("test_uploads", ignore_errors=True)
    shutil.rmtree("test_chroma", ignore_errors=True)


@pytest.fixture(autouse=True)
async def _fresh_connections():
    """Dispose pooled connections after each test.

    pytest-asyncio gives every test its own event loop; aiosqlite connections
    must not be reused across loops.
    """
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _get_or_create_user(badge_no: str, name: str, role: str, station: str) -> User:
    async with async_session_maker() as session:
        user = await session.scalar(select(User).where(User.badge_no == badge_no))
        if user is None:
            user = User(
                name=name,
                badge_no=badge_no,
                role=role,
                station=station,
                password=hash_password("demo123"),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


@pytest.fixture
async def io_user() -> User:
    return await _get_or_create_user("IO900", "Test IO Officer", "IO", "Test PS")


@pytest.fixture
async def sho_user() -> User:
    return await _get_or_create_user("SHO900", "Test SHO Officer", "SHO", "Test PS")


@pytest.fixture
def io_headers(io_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(io_user.id)}"}


@pytest.fixture
def sho_headers(sho_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(sho_user.id)}"}


@pytest.fixture
def make_case(client: AsyncClient, io_headers: dict[str, str]):
    """Factory posting a full CaseCreate payload (iron-rod assault narrative).

    Generates a unique FIR number per call; overrides merge on top of the
    default payload.
    """

    async def _make(**overrides) -> dict:
        payload = {
            "fir_number": f"FIR/TEST/{uuid.uuid4().hex[:8].upper()}",
            "station": "Navrangpura",
            "ps_name": "Navrangpura Police Station",
            "incident_date": "2026-07-05",
            "incident_time": "21:00:00",
            "incident_place": "CG Road, Navrangpura, Ahmedabad",
            "narrative": IRON_ROD_NARRATIVE,
            "language": "en",
            "persons": [
                {
                    "role": "ACCUSED",
                    "name": "Vikram Rathod",
                    "age": 28,
                    "gender": "M",
                    "address": "Naroda, Ahmedabad",
                },
                {
                    "role": "VICTIM",
                    "name": "Suresh Shah",
                    "age": 45,
                    "gender": "M",
                    "address": "Navrangpura, Ahmedabad",
                },
            ],
            "items": [
                {
                    "item_name": "Iron rod",
                    "quantity": "1",
                    "seized_from": "Scene of offence",
                }
            ],
            "sections": [
                {
                    "act": "BNS",
                    "section": "115",
                    "description": "Voluntarily causing hurt",
                    "source": "OFFICER_ADDED",
                }
            ],
        }
        payload.update(overrides)
        resp = await client.post("/api/v1/cases", json=payload, headers=io_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make
