from pydantic import BaseModel, Field


class SuggestRequest(BaseModel):
    narrative: str
    language: str = Field(default="en", pattern="^(gu|hi|en)$")


class SectionSuggestion(BaseModel):
    act: str
    section: str
    title: str
    relevance_score: float
    excerpt: str
    source: str = "AI_SUGGESTED"


class JudgmentSuggestion(BaseModel):
    title: str
    court: str
    year: int
    summary: str
    relevance_score: float


class ExtractedEntities(BaseModel):
    crime_types: list[str] = []
    weapons: list[str] = []
    persons: list[str] = []
    locations: list[str] = []
    dates: list[str] = []


class SuggestResponse(BaseModel):
    sections: list[SectionSuggestion]
    judgments: list[JudgmentSuggestion]
    entities: ExtractedEntities


class LegalSectionOut(BaseModel):
    act: str
    section: str
    title: str
    text: str


class TranslateRequest(BaseModel):
    text: str
    source: str = Field(pattern="^(gu|hi|en)$")
    target: str = Field(pattern="^(gu|hi|en)$")


class TranslateResponse(BaseModel):
    translated: str
    engine: str  # indictrans2 | google | passthrough
