import uuid

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.database import get_mongo_db, get_neo4j_driver
from app.models import collections as c
from app.models.common import utcnow
from app.modules.ingestion.graph_writer import write_repository_graph
from app.modules.learning_paths.service import complete_module, generate_learning_path, list_modules
from app.modules.notifications.service import (
    create_notification,
    list_notifications,
    mark_notification_read,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_and_list_notification_reflects_unread_count():
    user_id = ObjectId()
    workspace_id = ObjectId()
    try:
        await create_notification(
            user_id=str(user_id),
            workspace_id=str(workspace_id),
            type="module_completed",
            message="Test notification",
        )

        result = await list_notifications(user_id=str(user_id))
        assert len(result["notifications"]) == 1
        assert result["unreadCount"] == 1
        assert result["notifications"][0]["message"] == "Test notification"
        assert result["notifications"][0]["read"] is False
    finally:
        db = get_mongo_db()
        await db[c.NOTIFICATIONS].delete_many({"userId": user_id})


async def test_mark_notification_read_updates_unread_count():
    user_id = ObjectId()
    workspace_id = ObjectId()
    try:
        await create_notification(
            user_id=str(user_id),
            workspace_id=str(workspace_id),
            type="knowledge_gap",
            message="Gap notification",
        )
        result = await list_notifications(user_id=str(user_id))
        notification_id = result["notifications"][0]["id"]

        updated = await mark_notification_read(notification_id=notification_id, user_id=str(user_id))
        assert updated["read"] is True

        result = await list_notifications(user_id=str(user_id))
        assert result["unreadCount"] == 0
    finally:
        db = get_mongo_db()
        await db[c.NOTIFICATIONS].delete_many({"userId": user_id})


async def test_mark_notification_read_rejects_other_users_notification():
    user_id = ObjectId()
    other_user_id = ObjectId()
    workspace_id = ObjectId()
    try:
        await create_notification(
            user_id=str(user_id),
            workspace_id=str(workspace_id),
            type="module_completed",
            message="Private notification",
        )
        result = await list_notifications(user_id=str(user_id))
        notification_id = result["notifications"][0]["id"]

        with pytest.raises(HTTPException) as exc_info:
            await mark_notification_read(notification_id=notification_id, user_id=str(other_user_id))
        assert exc_info.value.status_code == 404
    finally:
        db = get_mongo_db()
        await db[c.NOTIFICATIONS].delete_many({"userId": user_id})


async def _seed_repo(repository_id: str):
    await write_repository_graph(
        repository_id=repository_id,
        github_url="https://github.com/test/notif-repo",
        parsed_docs=[
            {
                "filePath": "a.py",
                "language": "python",
                "components": [
                    {"name": "a_func", "type": "function", "startLine": 1, "endLine": 5,
                     "complexityScore": 5}
                ],
                "resolvedImports": [],
            }
        ],
    )


async def test_completing_entire_path_notifies_workspace_admins():
    repository_id = str(ObjectId())
    workspace_id = ObjectId()
    admin_id = ObjectId()
    dev_user_id = None
    profile_id = None
    try:
        await _seed_repo(repository_id)

        db = get_mongo_db()
        await db[c.USERS].insert_one(
            {
                "_id": admin_id,
                "email": f"notif-admin-{uuid.uuid4().hex[:8]}@test.prism",
                "passwordHash": "unused",
                "name": "Notif Admin",
                "role": "admin",
                "workspaceId": workspace_id,
                "createdAt": utcnow(),
                "lastLoginAt": None,
            }
        )

        dev_user_id = ObjectId()
        await db[c.USERS].insert_one(
            {
                "_id": dev_user_id,
                "email": f"notif-dev-{uuid.uuid4().hex[:8]}@test.prism",
                "passwordHash": "unused",
                "name": "Notif Dev",
                "role": "developer",
                "workspaceId": workspace_id,
                "createdAt": utcnow(),
                "lastLoginAt": None,
            }
        )
        profile_id = ObjectId()
        await db[c.DEVELOPER_PROFILES].insert_one(
            {
                "_id": profile_id,
                "userId": dev_user_id,
                "role": "developer",
                "assignedRepositoryId": ObjectId(repository_id),
                "experienceLevel": "senior",
                "skills": [],
                "startDate": utcnow(),
            }
        )

        path = await generate_learning_path(developer_profile_id=str(profile_id))
        modules = await list_modules(path_id=path["id"])
        assert len(modules) == 1  # single file repo -> single module

        await complete_module(module_id=modules[0]["id"], user_id=str(dev_user_id))

        notifications = await list_notifications(user_id=str(admin_id))
        path_completed = [
            n for n in notifications["notifications"] if n["type"] == "path_completed"
        ]
        assert len(path_completed) == 1
        assert "Notif Dev" in path_completed[0]["message"]
    finally:
        db = get_mongo_db()
        await db[c.NOTIFICATIONS].delete_many({"workspaceId": workspace_id})
        await db[c.USERS].delete_one({"_id": admin_id})
        if dev_user_id:
            await db[c.USERS].delete_one({"_id": dev_user_id})
        if profile_id:
            path_doc = await db[c.LEARNING_PATHS].find_one({"developerProfileId": profile_id})
            if path_doc:
                await db[c.LEARNING_MODULES].delete_many({"pathId": path_doc["_id"]})
                await db[c.LEARNING_PATHS].delete_one({"_id": path_doc["_id"]})
            await db[c.DEVELOPER_PROFILES].delete_one({"_id": profile_id})

        driver = get_neo4j_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (r:Repository {id: $repository_id})
                OPTIONAL MATCH (r)-[:HAS_FILE]->(f:File)
                OPTIONAL MATCH (f)-[:DEFINES]->(comp:CodeComponent)
                DETACH DELETE r, f, comp
                """,
                repository_id=repository_id,
            )
