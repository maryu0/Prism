from datetime import datetime

from pydantic import BaseModel, Field

from app.models.repository import RepositoryStatus


class ConnectRepositoryRequest(BaseModel):
    model_config = {"populate_by_name": True}

    github_url: str = Field(alias="githubUrl")
    access_token: str | None = Field(default=None, alias="accessToken")
    default_branch: str = Field(default="main", alias="defaultBranch")


class RepositoryResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    github_url: str = Field(alias="githubUrl")
    default_branch: str = Field(alias="defaultBranch")
    status: RepositoryStatus
    last_synced_at: datetime | None = Field(default=None, alias="lastSyncedAt")
    language_stats: dict[str, int] = Field(default_factory=dict, alias="languageStats")
    loc_count: int = Field(default=0, alias="locCount")


class RepositoryStatusResponse(BaseModel):
    model_config = {"populate_by_name": True}

    status: RepositoryStatus
    job_status: str | None = Field(default=None, alias="jobStatus")
    stats: dict = Field(default_factory=dict)
    error: str | None = None
