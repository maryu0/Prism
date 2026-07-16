from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    model_config = {"populate_by_name": True}

    actor_id: str = Field(alias="actorId")
    action: str
    target_type: str = Field(alias="targetType")
    target_id: str = Field(alias="targetId")
    timestamp: datetime


class AuditLogResponse(BaseModel):
    model_config = {"populate_by_name": True}

    entries: list[AuditLogEntry]
