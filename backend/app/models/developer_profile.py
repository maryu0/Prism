from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import MongoModel, PyObjectId, utcnow
from app.models.user import Role

ExperienceLevel = Literal["junior", "mid", "senior"]


class DeveloperProfile(MongoModel):
    user_id: PyObjectId = Field(alias="userId")

    # Copied from the invite token at signup — not user-writable.
    role: Role
    assigned_repository_id: PyObjectId = Field(alias="assignedRepositoryId")

    # The only field the developer actually self-reports.
    experience_level: ExperienceLevel = Field(alias="experienceLevel")

    skills: list[str] = Field(default_factory=list)
    start_date: datetime = Field(default_factory=utcnow, alias="startDate")
