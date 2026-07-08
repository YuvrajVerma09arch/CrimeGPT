from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserOut

DOC_TYPES = [
    "CHARGESHEET",
    "MEDICAL_LETTER",
    "REMAND_REQUEST",
    "SEIZURE_RECEIPT",
    "COURT_CUSTODY",
    "PANCHANAMA",
    "FACE_ID_FORM",
]


class GenerateDocumentsRequest(BaseModel):
    doc_types: list[str] = DOC_TYPES  # default: generate all 7


class GenerateDocumentsResponse(BaseModel):
    task_id: str
    status: str
    documents: list["DocumentOut"] = []


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    doc_type: str
    version: int
    docx_path: str | None = None
    pdf_path: str | None = None
    generator: UserOut | None = None
    generated_at: datetime
