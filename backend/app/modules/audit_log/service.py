from bson import ObjectId

from app.core.database import get_mongo_db
from app.models import collections as c

DEFAULT_LIMIT = 100


async def list_audit_log(*, workspace_id: str, limit: int = DEFAULT_LIMIT) -> dict:
    db = get_mongo_db()
    cursor = (
        db[c.AUDIT_LOGS]
        .find({"workspaceId": ObjectId(workspace_id)})
        .sort("timestamp", -1)
        .limit(limit)
    )
    entries = [
        {
            "actorId": str(doc["actorId"]),
            "action": doc["action"],
            "targetType": doc["targetType"],
            "targetId": doc["targetId"],
            "timestamp": doc["timestamp"],
        }
        async for doc in cursor
    ]
    return {"entries": entries}
