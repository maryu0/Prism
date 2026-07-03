from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db
from app.core.security import encrypt_secret
from app.models import collections as c
from app.models.common import utcnow
from app.worker.jobs import get_ingestion_queue, run_ingestion_job


async def connect_repository(
    *, workspace_id: str, github_url: str, access_token: str | None, default_branch: str
) -> dict:
    db = get_mongo_db()

    existing = await db[c.REPOSITORIES].find_one(
        {"workspaceId": ObjectId(workspace_id), "githubUrl": github_url}
    )
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This repository is already connected in this workspace"
        )

    repo_id = ObjectId()
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(workspace_id),
            "githubUrl": github_url,
            "defaultBranch": default_branch,
            "accessTokenEnc": encrypt_secret(access_token) if access_token else "",
            "status": "pending",
            "lastSyncedAt": None,
            "languageStats": {},
            "locCount": 0,
            "createdAt": utcnow(),
        }
    )

    await _enqueue_sync(repository_id=str(repo_id))
    return {"id": str(repo_id), "status": "pending"}


async def trigger_sync(*, repository_id: str, workspace_id: str) -> dict:
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(repository_id), "workspaceId": ObjectId(workspace_id)}
    )
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")
    if repo["status"] == "syncing":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A sync is already running for this repository"
        )

    return await _enqueue_sync(repository_id=repository_id)


async def _enqueue_sync(*, repository_id: str) -> dict:
    db = get_mongo_db()
    job_id = ObjectId()
    await db[c.INGESTION_JOBS].insert_one(
        {
            "_id": job_id,
            "repositoryId": ObjectId(repository_id),
            "type": "sync",
            "status": "queued",
            "startedAt": None,
            "finishedAt": None,
            "error": None,
            "stats": {},
            "createdAt": utcnow(),
        }
    )
    get_ingestion_queue().enqueue(
        run_ingestion_job, repository_id, str(job_id), job_timeout="10m"
    )
    return {"jobId": str(job_id)}


async def get_status(*, repository_id: str, workspace_id: str) -> dict:
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(repository_id), "workspaceId": ObjectId(workspace_id)}
    )
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    latest_job = await db[c.INGESTION_JOBS].find_one(
        {"repositoryId": ObjectId(repository_id)}, sort=[("createdAt", -1)]
    )

    return {
        "status": repo["status"],
        "jobStatus": latest_job["status"] if latest_job else None,
        "stats": latest_job["stats"] if latest_job else {},
        "error": latest_job.get("error") if latest_job else None,
    }
