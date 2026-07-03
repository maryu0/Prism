from datetime import datetime

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow


class AuditLog(MongoModel):
    workspace_id: PyObjectId = Field(alias="workspaceId")
    actor_id: PyObjectId = Field(alias="actorId")
    action: str
    target_type: str = Field(alias="targetType")
    target_id: str = Field(alias="targetId")
    timestamp: datetime = Field(default_factory=utcnow)
