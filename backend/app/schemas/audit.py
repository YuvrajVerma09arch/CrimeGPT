from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserOut


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    table_name: str | None = None
    record_id: str | None = None
    action: str | None = None
    old_data: dict | None = None
    new_data: dict | None = None
    changed_by: str | None = None
    user: UserOut | None = None
    changed_at: datetime
