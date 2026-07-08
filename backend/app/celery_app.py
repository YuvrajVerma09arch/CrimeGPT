"""Optional Celery application for async document generation.

Celery/Redis are OPTIONAL runtime dependencies. When celery is not installed
this module still imports cleanly and exposes ``celery_app = None`` and
``generate_documents_task = None`` so callers can feature-detect and fall
back to inline (synchronous) generation.
"""
from __future__ import annotations

from app.config import settings

try:
    from celery import Celery
except ImportError:  # celery not installed — inline generation fallback
    Celery = None  # type: ignore[assignment,misc]

if Celery is not None:
    celery_app = Celery(
        "crimegpt",
        broker=settings.redis_url,
        backend=settings.redis_url,
    )

    @celery_app.task(name="app.celery_app.generate_documents_task")
    def generate_documents_task(case_id: str, doc_types: list[str], user_id: str) -> list[str]:
        """Celery task: generate case documents in a worker process.

        Runs the async service inside asyncio.run with a fresh DB session
        and returns the generated Document row ids.
        """
        import asyncio

        from app.database import async_session_maker
        from app.services.document_service import generate_documents

        async def _run() -> list[str]:
            async with async_session_maker() as session:
                documents = await generate_documents(session, case_id, doc_types, user_id)
                return [d.id for d in documents]

        return asyncio.run(_run())

else:
    celery_app = None
    generate_documents_task = None
