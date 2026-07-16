from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db
from app.models import collections as c
from app.models.common import utcnow
from app.models.notification import NotificationType

LIST_LIMIT = 50


async def create_notification(
    *, user_id: str, workspace_id: str, type: NotificationType, message: str
) -> None:
    """Best-effort — a failure here must never block the real action (module
    completion, invite creation, etc.) that triggered it."""
    try:
        db = get_mongo_db()
        await db[c.NOTIFICATIONS].insert_one(
            {
                "userId": ObjectId(user_id),
                "workspaceId": ObjectId(workspace_id),
                "type": type,
                "message": message,
                "read": False,
                "createdAt": utcnow(),
            }
        )
    except Exception:  # noqa: BLE001
        pass


async def create_notification_for_admins(
    *, workspace_id: str, type: NotificationType, message: str
) -> None:
    """Fans a notification out to every admin in the workspace — used for
    events an admin should see regardless of who triggered them (a
    developer's milestone, a newly detected knowledge gap)."""
    db = get_mongo_db()
    admins = await db[c.USERS].find(
        {"workspaceId": ObjectId(workspace_id), "role": "admin"}
    ).to_list(length=None)
    for admin in admins:
        await create_notification(
            user_id=str(admin["_id"]), workspace_id=workspace_id, type=type, message=message
        )


async def list_notifications(*, user_id: str) -> dict:
    db = get_mongo_db()
    cursor = (
        db[c.NOTIFICATIONS]
        .find({"userId": ObjectId(user_id)})
        .sort("createdAt", -1)
        .limit(LIST_LIMIT)
    )
    docs = [doc async for doc in cursor]
    notifications = [
        {
            "id": str(doc["_id"]),
            "type": doc["type"],
            "message": doc["message"],
            "read": doc["read"],
            "createdAt": doc["createdAt"],
        }
        for doc in docs
    ]
    unread_count = sum(1 for doc in docs if not doc["read"])
    return {"notifications": notifications, "unreadCount": unread_count}


async def mark_notification_read(*, notification_id: str, user_id: str) -> dict:
    db = get_mongo_db()
    notification = await db[c.NOTIFICATIONS].find_one({"_id": ObjectId(notification_id)})
    if not notification or str(notification["userId"]) != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")

    await db[c.NOTIFICATIONS].update_one(
        {"_id": notification["_id"]}, {"$set": {"read": True}}
    )
    updated = await db[c.NOTIFICATIONS].find_one({"_id": notification["_id"]})
    return {
        "id": str(updated["_id"]),
        "type": updated["type"],
        "message": updated["message"],
        "read": updated["read"],
        "createdAt": updated["createdAt"],
    }
