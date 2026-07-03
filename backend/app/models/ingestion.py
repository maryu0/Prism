from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class IngestionJob(MongoModel):
    repository_id: PyObjectId = Field(alias="repositoryId")
    type: str
    status: JobStatus = "queued"
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    error: str | None = None
    stats: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
