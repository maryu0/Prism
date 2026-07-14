from datetime import datetime

from pydantic import BaseModel, Field


class LearningPathResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    developer_profile_id: str = Field(alias="developerProfileId")
    repository_id: str = Field(alias="repositoryId")
    status: str
    estimated_duration_minutes: int = Field(alias="estimatedDurationMinutes")
    adapted_count: int = Field(alias="adaptedCount")
    generated_at: datetime = Field(alias="generatedAt")


class LearningModuleResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    path_id: str = Field(alias="pathId")
    title: str
    description: str
    type: str
    target_entity_ids: list[str] = Field(alias="targetEntityIds")
    order: int
    prerequisites: list[str]
    status: str
    estimated_minutes: int = Field(alias="estimatedMinutes")
    completed_at: datetime | None = Field(default=None, alias="completedAt")


class GeneratePathRequest(BaseModel):
    model_config = {"populate_by_name": True}

    developer_profile_id: str = Field(alias="developerProfileId")


class CompleteModuleResponse(BaseModel):
    model_config = {"populate_by_name": True}

    module: LearningModuleResponse
    unlocked_module_ids: list[str] = Field(alias="unlockedModuleIds")
