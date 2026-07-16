from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.developer_profile import ExperienceLevel
from app.models.user import Role


class RegisterRequest(BaseModel):
    model_config = {"populate_by_name": True}

    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    invite_token: str | None = Field(default=None, alias="inviteToken")
    # Only meaningful (and required) when registering via an invite — an
    # admin registering standalone has no assigned repository to onboard
    # onto, so there's nothing for a learning path to be generated against.
    experience_level: ExperienceLevel | None = Field(default=None, alias="experienceLevel")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    model_config = {"populate_by_name": True}

    access_token: str = Field(alias="accessToken")


class InviteRequest(BaseModel):
    model_config = {"populate_by_name": True}

    email: EmailStr
    role: Role
    assigned_repository_id: str = Field(alias="assignedRepositoryId")


class InviteResponse(BaseModel):
    model_config = {"populate_by_name": True}

    invite_url: str = Field(alias="inviteUrl")
    expires_at: datetime = Field(alias="expiresAt")


class MeResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    email: EmailStr
    name: str
    role: Role
    workspace_id: str = Field(alias="workspaceId")
    assigned_repository_id: str | None = Field(default=None, alias="assignedRepositoryId")
