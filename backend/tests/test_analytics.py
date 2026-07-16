import uuid
from datetime import timedelta

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.database import get_mongo_db, get_neo4j_driver
from app.models import collections as c
from app.models.common import utcnow
from app.modules.analytics.schemas import (
    KnowledgeGapsResponse,
    MyProgressResponse,
    TeamProgressResponse,
)
from app.modules.analytics.service import get_knowledge_gaps, get_my_progress, get_team_progress
from app.modules.ingestion.graph_writer import write_repository_graph
from app.modules.learning_paths.service import complete_module, generate_learning_path, list_modules

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _seed_repo(repository_id: str):
    await write_repository_graph(
        repository_id=repository_id,
        github_url="https://github.com/test/repo",
        parsed_docs=[
            {
                "filePath": "a.py",
                "language": "python",
                "components": [
                    {"name": "a_func", "type": "function", "startLine": 1, "endLine": 5,
                     "complexityScore": 5}
                ],
                "resolvedImports": [],
            },
            {
                "filePath": "b.py",
                "language": "python",
                "components": [
                    {"name": "b_func", "type": "function", "startLine": 1, "endLine": 5,
                     "complexityScore": 5}
                ],
                "resolvedImports": ["a.py"],
            },
        ],
    )


async def _seed_developer(*, repository_id: str, workspace_id: ObjectId):
    db = get_mongo_db()
    user_id = ObjectId()
    await db[c.USERS].insert_one(
        {
            "_id": user_id,
            "email": f"learner-{uuid.uuid4().hex[:8]}@test.prism",
            "passwordHash": "unused",
            "name": "Test Learner",
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
            "userId": user_id,
            "role": "developer",
            "assignedRepositoryId": ObjectId(repository_id),
            "experienceLevel": "senior",
            "skills": [],
            "startDate": utcnow(),
        }
    )
    return user_id, profile_id


async def _cleanup(*, repository_id: str, user_ids: list[ObjectId], profile_ids: list[ObjectId]):
    db = get_mongo_db()
    for user_id in user_ids:
        await db[c.USERS].delete_one({"_id": user_id})
    for profile_id in profile_ids:
        path = await db[c.LEARNING_PATHS].find_one({"developerProfileId": profile_id})
        if path:
            await db[c.LEARNING_MODULES].delete_many({"pathId": path["_id"]})
            await db[c.LEARNING_PATHS].delete_one({"_id": path["_id"]})
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


async def test_get_my_progress_reflects_completed_modules():
    repository_id = str(ObjectId())
    user_id = profile_id = None
    try:
        await _seed_repo(repository_id)
        user_id, profile_id = await _seed_developer(
            repository_id=repository_id, workspace_id=ObjectId()
        )
        path = await generate_learning_path(developer_profile_id=str(profile_id))
        modules = await list_modules(path_id=path["id"])
        module_a = next(m for m in modules if m["targetEntityIds"] == [f"{repository_id}:a.py"])

        progress = await get_my_progress(user_id=str(user_id))
        MyProgressResponse.model_validate(progress)
        assert progress["modulesDone"] == 0
        assert progress["modulesTotal"] == 2
        assert progress["percentComplete"] == 0.0

        await complete_module(module_id=module_a["id"], user_id=str(user_id))

        progress = await get_my_progress(user_id=str(user_id))
        MyProgressResponse.model_validate(progress)
        assert progress["modulesDone"] == 1
        assert progress["percentComplete"] == 50.0
        assert progress["minutesSpent"] > 0
        assert progress["lastCompletedAt"] is not None
    finally:
        await _cleanup(
            repository_id=repository_id,
            user_ids=[user_id] if user_id else [],
            profile_ids=[profile_id] if profile_id else [],
        )


async def test_get_my_progress_404_when_no_active_path():
    fake_user_id = str(ObjectId())
    with pytest.raises(HTTPException) as exc_info:
        await get_my_progress(user_id=fake_user_id)
    assert exc_info.value.status_code == 404


async def test_get_team_progress_flags_stalled_member():
    repository_id = str(ObjectId())
    workspace_id = ObjectId()
    user_ids: list[ObjectId] = []
    profile_ids: list[ObjectId] = []
    try:
        await _seed_repo(repository_id)

        active_user_id, active_profile_id = await _seed_developer(
            repository_id=repository_id, workspace_id=workspace_id
        )
        user_ids.append(active_user_id)
        profile_ids.append(active_profile_id)
        await generate_learning_path(developer_profile_id=str(active_profile_id))

        stalled_user_id, stalled_profile_id = await _seed_developer(
            repository_id=repository_id, workspace_id=workspace_id
        )
        user_ids.append(stalled_user_id)
        profile_ids.append(stalled_profile_id)
        stalled_path = await generate_learning_path(developer_profile_id=str(stalled_profile_id))

        db = get_mongo_db()
        await db[c.LEARNING_PATHS].update_one(
            {"_id": ObjectId(stalled_path["id"])},
            {"$set": {"generatedAt": utcnow() - timedelta(days=10)}},
        )

        team = await get_team_progress(workspace_id=str(workspace_id))
        TeamProgressResponse.model_validate(team)
        assert len(team["members"]) == 2

        active_member = next(m for m in team["members"] if m["userId"] == str(active_user_id))
        stalled_member = next(m for m in team["members"] if m["userId"] == str(stalled_user_id))

        assert active_member["stalled"] is False
        assert stalled_member["stalled"] is True
    finally:
        await _cleanup(repository_id=repository_id, user_ids=user_ids, profile_ids=profile_ids)


async def test_get_knowledge_gaps_flags_module_stalled_across_multiple_developers():
    repository_id = str(ObjectId())
    workspace_id = ObjectId()
    user_ids: list[ObjectId] = []
    profile_ids: list[ObjectId] = []
    try:
        await _seed_repo(repository_id)

        # Both developers get a path against the same repo — since module titles
        # are the file path (deterministic), both will have an "a.py" module.
        for _ in range(2):
            user_id, profile_id = await _seed_developer(
                repository_id=repository_id, workspace_id=workspace_id
            )
            user_ids.append(user_id)
            profile_ids.append(profile_id)
            path = await generate_learning_path(developer_profile_id=str(profile_id))
            db = get_mongo_db()
            await db[c.LEARNING_MODULES].update_many(
                {"pathId": ObjectId(path["id"]), "status": "available"},
                {"$set": {"unlockedAt": utcnow() - timedelta(days=10)}},
            )

        gaps = await get_knowledge_gaps(workspace_id=str(workspace_id))
        KnowledgeGapsResponse.model_validate(gaps)

        a_py_gap = next((g for g in gaps["gaps"] if g["moduleTitle"] == "a.py"), None)
        assert a_py_gap is not None
        assert a_py_gap["stalledDeveloperCount"] == 2
        assert a_py_gap["repositoryId"] == repository_id
        assert a_py_gap["avgDaysStalled"] >= 9
    finally:
        await _cleanup(repository_id=repository_id, user_ids=user_ids, profile_ids=profile_ids)


async def test_get_knowledge_gaps_ignores_single_stalled_developer():
    repository_id = str(ObjectId())
    workspace_id = ObjectId()
    user_ids: list[ObjectId] = []
    profile_ids: list[ObjectId] = []
    try:
        await _seed_repo(repository_id)
        user_id, profile_id = await _seed_developer(
            repository_id=repository_id, workspace_id=workspace_id
        )
        user_ids.append(user_id)
        profile_ids.append(profile_id)
        path = await generate_learning_path(developer_profile_id=str(profile_id))
        db = get_mongo_db()
        await db[c.LEARNING_MODULES].update_many(
            {"pathId": ObjectId(path["id"]), "status": "available"},
            {"$set": {"unlockedAt": utcnow() - timedelta(days=10)}},
        )

        gaps = await get_knowledge_gaps(workspace_id=str(workspace_id))
        assert gaps["gaps"] == []
    finally:
        await _cleanup(repository_id=repository_id, user_ids=user_ids, profile_ids=profile_ids)
