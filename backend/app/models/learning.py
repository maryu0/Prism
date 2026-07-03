from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow

LearningPathStatus = Literal["active", "archived"]
ModuleType = Literal["code_area", "doc", "task"]
ModuleStatus = Literal["locked", "available", "in_progress", "done"]


class LearningPath(MongoModel):
    developer_profile_id: PyObjectId = Field(alias="developerProfileId")
    repository_id: PyObjectId = Field(alias="repositoryId")
    status: LearningPathStatus = "active"
    estimated_duration_minutes: int = Field(default=0, alias="estimatedDurationMinutes")
    adapted_count: int = Field(default=0, alias="adaptedCount")
    generated_at: datetime = Field(default_factory=utcnow, alias="generatedAt")


class LearningModule(MongoModel):
    path_id: PyObjectId = Field(alias="pathId")
    title: str
    description: str
    type: ModuleType
    target_entity_ids: list[str] = Field(default_factory=list, alias="targetEntityIds")
    order: int
    prerequisites: list[PyObjectId] = Field(default_factory=list)
    status: ModuleStatus = "locked"
    estimated_minutes: int = Field(default=0, alias="estimatedMinutes")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
