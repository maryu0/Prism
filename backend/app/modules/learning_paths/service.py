from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db
from app.models import collections as c
from app.models.common import utcnow
from app.modules.learning_paths.path_generator import build_modules, fetch_candidate_files
from app.modules.notifications.service import create_notification_for_admins


def _to_response(doc: dict) -> dict:
    """Mongo documents carry raw ObjectId/datetime values; response schemas
    expect plain strings for any id field. Converts every ObjectId (top-level
    or inside a list) generically rather than special-casing each field name,
    so a newly added id-typed field can't silently reintroduce this bug."""

    def convert(value):
        if isinstance(value, ObjectId):
            return str(value)
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value

    result = {k: convert(v) for k, v in doc.items()}
    result["id"] = str(doc["_id"])
    return result


async def generate_learning_path(*, developer_profile_id: str) -> dict:
    db = get_mongo_db()

    profile = await db[c.DEVELOPER_PROFILES].find_one({"_id": ObjectId(developer_profile_id)})
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Developer profile not found")

    existing = await db[c.LEARNING_PATHS].find_one(
        {"developerProfileId": profile["_id"], "status": "active"}
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "An active learning path already exists for this developer"
        )

    repository_id = str(profile["assignedRepositoryId"])
    candidates = await fetch_candidate_files(repository_id=repository_id)
    generated = build_modules(
        candidates=candidates, role=profile["role"], experience_level=profile["experienceLevel"]
    )

    path_id = ObjectId()
    await db[c.LEARNING_PATHS].insert_one(
        {
            "_id": path_id,
            "developerProfileId": profile["_id"],
            "repositoryId": profile["assignedRepositoryId"],
            "status": "active",
            "estimatedDurationMinutes": sum(m.estimated_minutes for m in generated),
            "adaptedCount": 0,
            "generatedAt": utcnow(),
        }
    )

    # Two passes: first insert every module to get its real _id, then patch
    # in prerequisites (which reference other modules' _ids) and unlock the
    # modules that have none.
    module_ids = [ObjectId() for _ in generated]
    now = utcnow()
    docs = [
        {
            "_id": module_ids[i],
            "pathId": path_id,
            "title": m.title,
            "description": m.description,
            "type": m.type,
            "targetEntityIds": m.target_entity_ids,
            "order": m.order,
            "prerequisites": [module_ids[idx] for idx in m.prerequisite_indices],
            "status": "available" if not m.prerequisite_indices else "locked",
            "estimatedMinutes": m.estimated_minutes,
            "completedAt": None,
            "unlockedAt": now if not m.prerequisite_indices else None,
        }
        for i, m in enumerate(generated)
    ]
    if docs:
        await db[c.LEARNING_MODULES].insert_many(docs)

    path = await db[c.LEARNING_PATHS].find_one({"_id": path_id})
    return _to_response(path)


async def get_learning_path(*, user_id: str) -> dict:
    db = get_mongo_db()

    profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": ObjectId(user_id)})
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No developer profile for this user")

    path = await db[c.LEARNING_PATHS].find_one(
        {"developerProfileId": profile["_id"], "status": "active"}
    )
    if not path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active learning path")

    return _to_response(path)


async def list_modules(*, path_id: str) -> list[dict]:
    db = get_mongo_db()
    cursor = db[c.LEARNING_MODULES].find({"pathId": ObjectId(path_id)}).sort("order", 1)
    return [_to_response(doc) async for doc in cursor]


async def complete_module(*, module_id: str, user_id: str) -> dict:
    db = get_mongo_db()

    module = await db[c.LEARNING_MODULES].find_one({"_id": ObjectId(module_id)})
    if not module:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module not found")

    path = await db[c.LEARNING_PATHS].find_one({"_id": module["pathId"]})
    profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": ObjectId(user_id)})
    if not path or not profile or path["developerProfileId"] != profile["_id"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This module does not belong to you")

    await db[c.LEARNING_MODULES].update_one(
        {"_id": module["_id"]}, {"$set": {"status": "done", "completedAt": utcnow()}}
    )

    all_modules = await db[c.LEARNING_MODULES].find({"pathId": path["_id"]}).to_list(length=None)
    done_ids = {m["_id"] for m in all_modules if m["_id"] == module["_id"] or m["status"] == "done"}

    unlocked_ids: list[str] = []
    for m in all_modules:
        if m["status"] == "locked" and all(p in done_ids for p in m["prerequisites"]):
            await db[c.LEARNING_MODULES].update_one(
                {"_id": m["_id"]}, {"$set": {"status": "available", "unlockedAt": utcnow()}}
            )
            unlocked_ids.append(str(m["_id"]))

    all_done = all(
        m["_id"] == module["_id"] or m["status"] == "done" for m in all_modules
    )
    if all_done:
        user = await db[c.USERS].find_one({"_id": ObjectId(user_id)})
        if user:
            await create_notification_for_admins(
                workspace_id=str(user["workspaceId"]),
                type="path_completed",
                message=f"{user['name']} completed their learning path.",
            )

    updated_module = await db[c.LEARNING_MODULES].find_one({"_id": module["_id"]})
    return {"module": _to_response(updated_module), "unlockedModuleIds": unlocked_ids}
