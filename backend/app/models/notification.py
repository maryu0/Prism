from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow

NotificationType = Literal["module_completed", "path_completed", "knowledge_gap"]


class Notification(MongoModel):
    user_id: PyObjectId = Field(alias="userId")
    workspace_id: PyObjectId = Field(alias="workspaceId")
    type: NotificationType
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
