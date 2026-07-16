from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    model_config = {"populate_by_name": True}

    id: str
    type: str
    message: str
    read: bool
    created_at: datetime = Field(alias="createdAt")


class NotificationListResponse(BaseModel):
    model_config = {"populate_by_name": True}

    notifications: list[NotificationResponse]
    unread_count: int = Field(alias="unreadCount")
