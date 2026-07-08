"""Legal intelligence endpoints: RAG suggestions and corpus search/lookup."""
from fastapi import APIRouter, Depends, HTTPException, Query

from app.rag import pipeline
from app.schemas.legal import LegalSectionOut, SuggestRequest, SuggestResponse
from app.services import legal_service
from app.utils.security import get_current_user

router = APIRouter(
    prefix="/legal",
    tags=["legal"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/suggest", response_model=SuggestResponse)
async def suggest(payload: SuggestRequest) -> SuggestResponse:
    """Run the narrative through the RAG pipeline and suggest BNS/BNSS/BSA sections."""
    result = await pipeline.suggest_legal_sections(payload.narrative, payload.language)
    return SuggestResponse.model_validate(result)


@router.get("/search", response_model=list[LegalSectionOut])
async def search_sections(
    q: str = Query(min_length=1),
    act: str | None = Query(default=None, pattern="^(BNS|BNSS|BSA)$"),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[LegalSectionOut]:
    """Keyword search over the indexed legal corpus, optionally scoped to one act."""
    results = legal_service.search_sections(q, act=act, limit=limit)
    return [LegalSectionOut.model_validate(r) for r in results]


@router.get("/section/{act}/{number}", response_model=LegalSectionOut)
async def get_section(act: str, number: str) -> LegalSectionOut:
    """Return the full text of a single legal section."""
    section = legal_service.get_section(act, number)
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found")
    return LegalSectionOut.model_validate(section)
