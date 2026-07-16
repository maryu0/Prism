from bson import ObjectId

from app.core.database import get_mongo_db
from app.models import collections as c
from app.models.common import utcnow


async def log_action(
    *, workspace_id: str, actor_id: str, action: str, target_type: str, target_id: str
) -> None:
    """Best-effort security/audit trail — never blocks or fails the caller's
    real operation, since a logging failure must not prevent e.g. an invite
    from being created."""
    try:
        db = get_mongo_db()
        await db[c.AUDIT_LOGS].insert_one(
            {
                "workspaceId": ObjectId(workspace_id),
                "actorId": ObjectId(actor_id),
                "action": action,
                "targetType": target_type,
                "targetId": target_id,
                "timestamp": utcnow(),
            }
        )
    except Exception:  # noqa: BLE001
        pass
