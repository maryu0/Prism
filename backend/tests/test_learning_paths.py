import uuid

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.database import get_mongo_db, get_neo4j_driver
from app.models import collections as c
from app.models.common import utcnow
from app.modules.ingestion.graph_writer import write_repository_graph
from app.modules.learning_paths.schemas import LearningModuleResponse, LearningPathResponse
from app.modules.learning_paths.service import (
    complete_module,
    generate_learning_path,
    get_learning_path,
    list_modules,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _cleanup(*, repository_id: str, user_id: ObjectId, profile_id: ObjectId | None):
    db = get_mongo_db()
    await db[c.USERS].delete_one({"_id": user_id})
    if profile_id:
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


async def _seed_developer_profile(*, repository_id: str, role: str, experience_level: str):
    db = get_mongo_db()
    user_id = ObjectId()
    await db[c.USERS].insert_one(
        {
            "_id": user_id,
            "email": f"learner-{uuid.uuid4().hex[:8]}@test.prism",
            "passwordHash": "unused",
            "name": "Test Learner",
            "role": role,
            "workspaceId": ObjectId(),
            "createdAt": utcnow(),
            "lastLoginAt": None,
        }
    )
    profile_id = ObjectId()
    await db[c.DEVELOPER_PROFILES].insert_one(
        {
            "_id": profile_id,
            "userId": user_id,
            "role": role,
            "assignedRepositoryId": ObjectId(repository_id),
            "experienceLevel": experience_level,
            "skills": [],
            "startDate": utcnow(),
        }
    )
    return user_id, profile_id


async def test_generate_learning_path_orders_by_dependency_and_unlocks_root():
    repository_id = str(ObjectId())
    user_id = profile_id = None
    try:
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
        user_id, profile_id = await _seed_developer_profile(
            repository_id=repository_id, role="developer", experience_level="senior"
        )

        path = await generate_learning_path(developer_profile_id=str(profile_id))
        # Round-tripping through the actual response schema (what FastAPI's
        # serialize_response does) catches unstringified ObjectId fields that
        # a plain dict assertion on the service's raw return value would miss.
        LearningPathResponse.model_validate(path)
        assert path["status"] == "active"
        assert path["estimatedDurationMinutes"] > 0

        modules = await list_modules(path_id=path["id"])
        for m in modules:
            LearningModuleResponse.model_validate(m)
        module_a = next(m for m in modules if m["targetEntityIds"] == [f"{repository_id}:a.py"])
        module_b = next(m for m in modules if m["targetEntityIds"] == [f"{repository_id}:b.py"])

        assert module_a["order"] < module_b["order"]
        assert module_a["status"] == "available"  # no prerequisites -> unlocked immediately
        assert module_b["status"] == "locked"  # depends on a -> starts locked
        assert module_a["id"] in module_b["prerequisites"]
    finally:
        await _cleanup(repository_id=repository_id, user_id=user_id, profile_id=profile_id)


async def test_generate_learning_path_rejects_duplicate_active_path():
    repository_id = str(ObjectId())
    user_id = profile_id = None
    try:
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
                }
            ],
        )
        user_id, profile_id = await _seed_developer_profile(
            repository_id=repository_id, role="developer", experience_level="senior"
        )

        await generate_learning_path(developer_profile_id=str(profile_id))

        with pytest.raises(HTTPException) as exc_info:
            await generate_learning_path(developer_profile_id=str(profile_id))
        assert exc_info.value.status_code == 409
    finally:
        await _cleanup(repository_id=repository_id, user_id=user_id, profile_id=profile_id)


async def test_complete_module_unlocks_dependent_module():
    repository_id = str(ObjectId())
    user_id = profile_id = None
    try:
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
        user_id, profile_id = await _seed_developer_profile(
            repository_id=repository_id, role="developer", experience_level="senior"
        )

        path = await generate_learning_path(developer_profile_id=str(profile_id))
        modules = await list_modules(path_id=path["id"])
        module_a = next(m for m in modules if m["targetEntityIds"] == [f"{repository_id}:a.py"])
        module_b = next(m for m in modules if m["targetEntityIds"] == [f"{repository_id}:b.py"])

        assert module_b["status"] == "locked"

        result = await complete_module(module_id=module_a["id"], user_id=str(user_id))
        LearningModuleResponse.model_validate(result["module"])

        assert result["module"]["status"] == "done"
        assert module_b["id"] in result["unlockedModuleIds"]

        refreshed = await list_modules(path_id=path["id"])
        refreshed_b = next(m for m in refreshed if m["id"] == module_b["id"])
        assert refreshed_b["status"] == "available"
    finally:
        await _cleanup(repository_id=repository_id, user_id=user_id, profile_id=profile_id)


async def test_complete_module_rejects_other_users_module():
    repository_id = str(ObjectId())
    user_id = profile_id = None
    other_user_id = None
    try:
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
                }
            ],
        )
        user_id, profile_id = await _seed_developer_profile(
            repository_id=repository_id, role="developer", experience_level="senior"
        )
        other_user_id, other_profile_id = await _seed_developer_profile(
            repository_id=repository_id, role="developer", experience_level="senior"
        )

        path = await generate_learning_path(developer_profile_id=str(profile_id))
        modules = await list_modules(path_id=path["id"])
        module_a = modules[0]

        with pytest.raises(HTTPException) as exc_info:
            await complete_module(module_id=module_a["id"], user_id=str(other_user_id))
        assert exc_info.value.status_code == 403

        db = get_mongo_db()
        await db[c.USERS].delete_one({"_id": other_user_id})
        await db[c.DEVELOPER_PROFILES].delete_one({"_id": other_profile_id})
    finally:
        await _cleanup(repository_id=repository_id, user_id=user_id, profile_id=profile_id)


async def test_get_learning_path_404_when_none_exists():
    fake_user_id = str(ObjectId())
    with pytest.raises(HTTPException) as exc_info:
        await get_learning_path(user_id=fake_user_id)
    assert exc_info.value.status_code == 404
