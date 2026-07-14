import asyncio

from bson import ObjectId

from app.core.database import get_mongo_db
from app.models import collections as c
from app.modules.search.index_writer import search_components


async def search_workspace_code(*, workspace_id: str, query: str, limit: int) -> list[dict]:
    """Restricts semantic search to repositories belonging to the caller's
    workspace — otherwise every workspace would be searching the same shared
    Chroma collection with no isolation between tenants."""
    db = get_mongo_db()
    repo_ids = await db[c.REPOSITORIES].distinct(
        "_id", {"workspaceId": ObjectId(workspace_id)}
    )
    repo_id_strings = [str(rid) for rid in repo_ids]

    return await asyncio.to_thread(
        search_components,
        workspace_repository_ids=repo_id_strings,
        query=query,
        limit=limit,
    )
