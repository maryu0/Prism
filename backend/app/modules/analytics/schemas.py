from datetime import datetime

from pydantic import BaseModel, Field


class MyProgressResponse(BaseModel):
    model_config = {"populate_by_name": True}

    path_id: str = Field(alias="pathId")
    modules_done: int = Field(alias="modulesDone")
    modules_total: int = Field(alias="modulesTotal")
    percent_complete: float = Field(alias="percentComplete")
    minutes_spent: int = Field(alias="minutesSpent")
    minutes_remaining: int = Field(alias="minutesRemaining")
    last_completed_at: datetime | None = Field(default=None, alias="lastCompletedAt")


class TeamMemberProgress(BaseModel):
    model_config = {"populate_by_name": True}

    user_id: str = Field(alias="userId")
    name: str
    role: str
    repository_id: str = Field(alias="repositoryId")
    modules_done: int = Field(alias="modulesDone")
    modules_total: int = Field(alias="modulesTotal")
    percent_complete: float = Field(alias="percentComplete")
    last_completed_at: datetime | None = Field(default=None, alias="lastCompletedAt")
    stalled: bool


class TeamProgressResponse(BaseModel):
    model_config = {"populate_by_name": True}

    members: list[TeamMemberProgress]


class KnowledgeGap(BaseModel):
    model_config = {"populate_by_name": True}

    repository_id: str = Field(alias="repositoryId")
    module_title: str = Field(alias="moduleTitle")
    stalled_developer_count: int = Field(alias="stalledDeveloperCount")
    avg_days_stalled: float = Field(alias="avgDaysStalled")


class KnowledgeGapsResponse(BaseModel):
    model_config = {"populate_by_name": True}

    gaps: list[KnowledgeGap]
