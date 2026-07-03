from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.common import MongoModel, PyObjectId, utcnow
from app.models.user import Role


class InviteToken(BaseModel):
    token: str
    email: EmailStr
    role: Role
    assigned_repository_id: PyObjectId = Field(alias="assignedRepositoryId")
    expires_at: datetime = Field(alias="expiresAt")
    used: bool = False

    model_config = {"populate_by_name": True}


class Workspace(MongoModel):
    name: str
    owner_id: PyObjectId = Field(alias="ownerId")
    invite_tokens: list[InviteToken] = Field(default_factory=list, alias="inviteTokens")
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
