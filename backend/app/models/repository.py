from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow

RepositoryStatus = Literal["pending", "syncing", "ready", "error"]


class Repository(MongoModel):
    workspace_id: PyObjectId = Field(alias="workspaceId")
    github_url: str = Field(alias="githubUrl")
    default_branch: str = Field(default="main", alias="defaultBranch")
    access_token_enc: str = Field(alias="accessTokenEnc")
    status: RepositoryStatus = "pending"
    last_synced_at: datetime | None = Field(default=None, alias="lastSyncedAt")
    language_stats: dict[str, int] = Field(default_factory=dict, alias="languageStats")
    loc_count: int = Field(default=0, alias="locCount")
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
