"""Document generation, listing, download and bulk-download endpoints."""
import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import (
    DOC_TYPES,
    DocumentOut,
    GenerateDocumentsRequest,
    GenerateDocumentsResponse,
)
from app.services import case_service, document_service
from app.utils.security import get_current_user

# Celery is optional at runtime — fall back to synchronous generation.
try:  # pragma: no cover - exercised only when celery is installed
    from app.celery_app import celery_app, generate_documents_task
except Exception:  # noqa: BLE001
    celery_app = None
    generate_documents_task = None

router = APIRouter(tags=["documents"], dependencies=[Depends(get_current_user)])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MEDIA_TYPE = "application/pdf"


@router.post(
    "/cases/{case_id}/documents/generate", response_model=GenerateDocumentsResponse
)
async def generate_documents(
    case_id: str,
    payload: GenerateDocumentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateDocumentsResponse:
    """Generate the requested legal documents for a case.

    Queues a Celery task when configured; otherwise renders synchronously.
    """
    doc_types = payload.doc_types or list(DOC_TYPES)
    unknown = [d for d in doc_types if d not in DOC_TYPES]
    if unknown:
        raise HTTPException(
            status_code=400, detail=f"Unknown doc_types: {', '.join(unknown)}"
        )

    # 404 early if the case is missing or soft-deleted.
    await case_service.get_case(db, case_id)

    if settings.use_celery and celery_app is not None and generate_documents_task is not None:
        result = generate_documents_task.delay(case_id, doc_types, current_user.id)
        return GenerateDocumentsResponse(
            task_id=str(result.id), status="queued", documents=[]
        )

    documents = await document_service.generate_documents(
        db, case_id, doc_types, current_user.id
    )
    return GenerateDocumentsResponse(
        task_id=str(uuid4()),
        status="completed",
        documents=[DocumentOut.model_validate(d) for d in documents],
    )


@router.get("/cases/{case_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    case_id: str, db: AsyncSession = Depends(get_db)
) -> list[DocumentOut]:
    """List all generated documents for a case (newest versions included)."""
    case = await case_service.get_case(db, case_id)
    return [DocumentOut.model_validate(d) for d in case.documents]


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: str,
    format: str = Query(default="docx", pattern="^(docx|pdf)$"),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Stream a generated document file in DOCX (default) or PDF format."""
    document = await db.scalar(select(Document).where(Document.id == doc_id))
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if format == "pdf":
        path = document.pdf_path
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="PDF not available")
        media_type = PDF_MEDIA_TYPE
    else:
        path = document.docx_path
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        media_type = DOCX_MEDIA_TYPE

    filename = f"{document.doc_type.lower()}_v{document.version}.{format}"
    return FileResponse(path=path, media_type=media_type, filename=filename)


@router.post("/cases/{case_id}/documents/bulk-download")
async def bulk_download(case_id: str, db: AsyncSession = Depends(get_db)) -> Response:
    """Download every generated document for a case as a single ZIP archive."""
    case = await case_service.get_case(db, case_id)
    documents = list(case.documents)
    if not documents:
        raise HTTPException(status_code=404, detail="No documents generated yet")

    zip_bytes = document_service.zip_documents(documents)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="fir_documents.zip"'},
    )
