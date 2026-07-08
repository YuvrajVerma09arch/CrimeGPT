"""Translation endpoint — Gujarati / Hindi / English via IndicTrans2 with fallbacks."""
from fastapi import APIRouter, Depends

from app.schemas.legal import TranslateRequest, TranslateResponse
from app.services import translation_service
from app.utils.security import get_current_user

router = APIRouter(tags=["translate"], dependencies=[Depends(get_current_user)])


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(payload: TranslateRequest) -> TranslateResponse:
    """Translate text between gu/hi/en; reports which engine produced the result."""
    translated, engine = await translation_service.translate(
        payload.text, payload.source, payload.target
    )
    return TranslateResponse(translated=translated, engine=engine)
