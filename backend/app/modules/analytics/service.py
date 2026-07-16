from datetime import timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db
from app.models import collections as c
from app.models.common import utcnow
from app.modules.notifications.service import create_notification_for_admins

STALLED_AFTER = timedelta(days=3)
GAP_MIN_STALLED_DEVELOPERS = 2


async def get_my_progress(*, user_id: str) -> dict:
    db = get_mongo_db()

    profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": ObjectId(user_id)})
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No developer profile for this user")

    path = await db[c.LEARNING_PATHS].find_one(
        {"developerProfileId": profile["_id"], "status": "active"}
    )
    if not path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active learning path")

    modules = await db[c.LEARNING_MODULES].find({"pathId": path["_id"]}).to_list(length=None)
    done = [m for m in modules if m["status"] == "done"]
    completed_ats = [m["completedAt"] for m in done if m["completedAt"] is not None]

    minutes_spent = sum(m["estimatedMinutes"] for m in done)
    minutes_total = sum(m["estimatedMinutes"] for m in modules)

    return {
        "pathId": str(path["_id"]),
        "modulesDone": len(done),
        "modulesTotal": len(modules),
        "percentComplete": round(100 * len(done) / len(modules), 1) if modules else 0.0,
        "minutesSpent": minutes_spent,
        "minutesRemaining": max(minutes_total - minutes_spent, 0),
        "lastCompletedAt": max(completed_ats) if completed_ats else None,
    }


async def get_team_progress(*, workspace_id: str) -> dict:
    db = get_mongo_db()

    users = await db[c.USERS].find({"workspaceId": ObjectId(workspace_id)}).to_list(length=None)
    now = utcnow()

    members = []
    for user in users:
        profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": user["_id"]})
        if not profile:
            continue

        path = await db[c.LEARNING_PATHS].find_one(
            {"developerProfileId": profile["_id"], "status": "active"}
        )
        if not path:
            continue

        modules = await db[c.LEARNING_MODULES].find({"pathId": path["_id"]}).to_list(length=None)
        done = [m for m in modules if m["status"] == "done"]
        completed_ats = [m["completedAt"] for m in done if m["completedAt"] is not None]
        last_completed_at = max(completed_ats) if completed_ats else None
        is_complete = bool(modules) and len(done) == len(modules)

        reference_time = last_completed_at or path["generatedAt"]
        stalled = not is_complete and (now - reference_time) > STALLED_AFTER

        members.append(
            {
                "userId": str(user["_id"]),
                "name": user["name"],
                "role": profile["role"],
                "repositoryId": str(profile["assignedRepositoryId"]),
                "modulesDone": len(done),
                "modulesTotal": len(modules),
                "percentComplete": round(100 * len(done) / len(modules), 1) if modules else 0.0,
                "lastCompletedAt": last_completed_at,
                "stalled": stalled,
            }
        )

    return {"members": members}


async def get_knowledge_gaps(*, workspace_id: str) -> dict:
    """Surfaces modules where multiple developers are stuck (unlocked, not yet
    completed, for longer than STALLED_AFTER) — a signal that the underlying
    file/concept is a genuine onboarding bottleneck rather than one developer's
    pace. Modules are grouped by (repositoryId, title) since each developer's
    learning path generates its own module documents; file-based module titles
    are deterministic per repository (see path_generator.py), so the same file
    across developers shares a title and can be grouped even without a shared
    module _id."""
    db = get_mongo_db()

    users = await db[c.USERS].find({"workspaceId": ObjectId(workspace_id)}).to_list(length=None)
    now = utcnow()

    stalled_by_key: dict[tuple[str, str], list[float]] = {}
    for user in users:
        profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": user["_id"]})
        if not profile:
            continue

        path = await db[c.LEARNING_PATHS].find_one(
            {"developerProfileId": profile["_id"], "status": "active"}
        )
        if not path:
            continue

        modules = await db[c.LEARNING_MODULES].find(
            {"pathId": path["_id"], "status": "available", "unlockedAt": {"$ne": None}}
        ).to_list(length=None)

        repository_id = str(profile["assignedRepositoryId"])
        for m in modules:
            days_stalled = (now - m["unlockedAt"]).total_seconds() / 86400
            if (now - m["unlockedAt"]) <= STALLED_AFTER:
                continue
            key = (repository_id, m["title"])
            stalled_by_key.setdefault(key, []).append(days_stalled)

    gaps = [
        {
            "repositoryId": repo_id,
            "moduleTitle": title,
            "stalledDeveloperCount": len(days_list),
            "avgDaysStalled": round(sum(days_list) / len(days_list), 1),
        }
        for (repo_id, title), days_list in stalled_by_key.items()
        if len(days_list) >= GAP_MIN_STALLED_DEVELOPERS
    ]
    gaps.sort(key=lambda g: g["stalledDeveloperCount"], reverse=True)

    await _notify_new_gaps(workspace_id=workspace_id, gaps=gaps)

    return {"gaps": gaps}


async def _notify_new_gaps(*, workspace_id: str, gaps: list[dict]) -> None:
    """Notifies admins only once per (repository, module) gap — re-fetching
    this endpoint repeatedly (e.g. an admin revisiting the dashboard) must not
    re-send the same alert every time. A workspace-level `notifiedGaps` set
    tracks what's already been announced, avoiding a new collection for a
    single small dedup set."""
    if not gaps:
        return

    db = get_mongo_db()
    workspace = await db[c.WORKSPACES].find_one({"_id": ObjectId(workspace_id)})
    if not workspace:
        return

    already_notified = set(workspace.get("notifiedGaps", []))
    new_gap_keys = [
        f"{g['repositoryId']}:{g['moduleTitle']}"
        for g in gaps
        if f"{g['repositoryId']}:{g['moduleTitle']}" not in already_notified
    ]
    if not new_gap_keys:
        return

    for gap in gaps:
        key = f"{gap['repositoryId']}:{gap['moduleTitle']}"
        if key not in new_gap_keys:
            continue
        await create_notification_for_admins(
            workspace_id=workspace_id,
            type="knowledge_gap",
            message=(
                f"{gap['stalledDeveloperCount']} developers are stuck on "
                f"\"{gap['moduleTitle']}\" — possible knowledge gap."
            ),
        )

    await db[c.WORKSPACES].update_one(
        {"_id": ObjectId(workspace_id)}, {"$addToSet": {"notifiedGaps": {"$each": new_gap_keys}}}
    )
