"""OCR endpoint (bonus) — extract text from scanned/handwritten FIR images."""
import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.config import settings
from app.utils.ocr import TESSERACT_AVAILABLE, extract_text
from app.utils.security import get_current_user

router = APIRouter(prefix="/ocr", tags=["ocr"], dependencies=[Depends(get_current_user)])


@router.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    """Run Tesseract OCR on an uploaded image and return text + confidence."""
    if not TESSERACT_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="OCR not available on this deployment"
        )

    suffix = Path(file.filename).suffix.lower() if file.filename else ""
    if len(suffix) > 10 or not suffix.replace(".", "").isalnum():
        suffix = ""

    dest_dir = Path(settings.upload_dir) / "ocr"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4()}{suffix}"
    dest.write_bytes(await file.read())

    text, confidence = await asyncio.to_thread(extract_text, str(dest))
    return {"extracted_text": text, "confidence": confidence}
