from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from app.models.common import MongoModel, PyObjectId, utcnow

Role = Literal["admin", "senior", "developer"]


class User(MongoModel):
    email: EmailStr
    password_hash: str = Field(alias="passwordHash")
    name: str
    role: Role
    workspace_id: PyObjectId = Field(alias="workspaceId")
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
    last_login_at: datetime | None = Field(default=None, alias="lastLoginAt")
