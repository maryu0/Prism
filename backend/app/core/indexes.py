from pymongo import ASCENDING, IndexModel

from app.core.database import get_mongo_db
from app.models import collections as c


async def create_mongo_indexes() -> dict[str, list[str]]:
    """Idempotent — safe to run on every startup/deploy, not just once."""
    db = get_mongo_db()

    plan: dict[str, list[IndexModel]] = {
        c.USERS: [
            IndexModel([("email", ASCENDING)], unique=True, name="uniq_email"),
            IndexModel([("workspaceId", ASCENDING)], name="by_workspace"),
        ],
        c.REPOSITORIES: [
            IndexModel([("workspaceId", ASCENDING)], name="by_workspace"),
        ],
        c.DEVELOPER_PROFILES: [
            IndexModel([("userId", ASCENDING)], unique=True, name="uniq_user"),
        ],
        c.LEARNING_PATHS: [
            IndexModel([("developerProfileId", ASCENDING)], name="by_profile"),
        ],
        c.LEARNING_MODULES: [
            IndexModel([("pathId", ASCENDING)], name="by_path"),
        ],
        c.CHAT_SESSIONS: [
            IndexModel([("userId", ASCENDING), ("createdAt", ASCENDING)], name="by_user_created"),
        ],
        c.CHAT_MESSAGES: [
            IndexModel(
                [("sessionId", ASCENDING), ("createdAt", ASCENDING)], name="by_session_created"
            ),
        ],
        c.INGESTION_JOBS: [
            IndexModel([("repositoryId", ASCENDING)], name="by_repository"),
        ],
        c.AUDIT_LOGS: [
            IndexModel(
                [("workspaceId", ASCENDING), ("timestamp", ASCENDING)], name="by_workspace_time"
            ),
        ],
    }

    created: dict[str, list[str]] = {}
    for collection_name, indexes in plan.items():
        names = await db[collection_name].create_indexes(indexes)
        created[collection_name] = names
    return created
