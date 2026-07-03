from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.common import MongoModel, PyObjectId, utcnow

MessageRole = Literal["user", "assistant"]
Feedback = Literal["up", "down"]


class Citation(BaseModel):
    file_path: str = Field(alias="filePath")
    start_line: int = Field(alias="startLine")
    end_line: int = Field(alias="endLine")
    url: str

    model_config = {"populate_by_name": True}


class ChatSession(MongoModel):
    user_id: PyObjectId = Field(alias="userId")
    repository_id: PyObjectId = Field(alias="repositoryId")
    title: str
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")


class ChatMessage(MongoModel):
    session_id: PyObjectId = Field(alias="sessionId")
    role: MessageRole
    content: str
    citations: list[Citation] = Field(default_factory=list)
    feedback: Feedback | None = None
    created_at: datetime = Field(default_factory=utcnow, alias="createdAt")
