"""CrimeGPT FastAPI application entrypoint.

Wires all routers under /api/v1, configures CORS, and bootstraps the
database, audit listeners, legal corpus and document templates at startup.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import audit, auth, cases, diary, documents, legal, ocr, translate

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup: create tables, register audit listeners, warm the legal corpus."""
    await init_db()

    # Importing registers the SQLAlchemy after_flush audit listeners.
    from app.utils import audit as _audit_listeners  # noqa: F401

    from app.services import document_service, legal_service

    legal_service.load_corpus()

    try:
        document_service.ensure_templates()
    except Exception:  # noqa: BLE001 — template bootstrap must never kill startup
        logger.exception("Failed to build .docx templates at startup")

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    yield


app = FastAPI(
    title="CrimeGPT API",
    version="1.0.0",
    description="AI-powered crime documentation and legal intelligence platform.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")
api.include_router(auth.router)
api.include_router(cases.router)
api.include_router(documents.router)
api.include_router(legal.router)
api.include_router(diary.router)
api.include_router(audit.router)
api.include_router(translate.router)
api.include_router(ocr.router)
app.include_router(api)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Liveness probe — no auth, no prefix."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all: log the traceback, return a generic 500 without leaking internals."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
