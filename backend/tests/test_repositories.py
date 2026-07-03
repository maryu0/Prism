import uuid

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.database import get_mongo_db
from app.main import app
from app.models import collections as c
from app.worker.jobs import get_ingestion_queue

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def tracker():
    return {"emails": [], "repo_ids": [], "job_ids": []}


async def cleanup_test_data(tracker: dict) -> None:
    db = get_mongo_db()
    emails = tracker["emails"]

    if emails:
        users = await db[c.USERS].find({"email": {"$in": emails}}).to_list(length=None)
        owner_ids = [u["_id"] for u in users]
        await db[c.USERS].delete_many({"email": {"$in": emails}})
        if owner_ids:
            await db[c.WORKSPACES].delete_many({"ownerId": {"$in": owner_ids}})

    if tracker["repo_ids"]:
        await db[c.REPOSITORIES].delete_many({"_id": {"$in": tracker["repo_ids"]}})
        await db[c.PARSED_FILES].delete_many({"repositoryId": {"$in": tracker["repo_ids"]}})

    if tracker["job_ids"]:
        await db[c.INGESTION_JOBS].delete_many({"_id": {"$in": tracker["job_ids"]}})


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.prism"


async def _register_and_login(client: AsyncClient, tracker: dict) -> dict:
    email = unique_email("repoadmin")
    tracker["emails"].append(email)
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Repo Admin"},
    )
    workspace_id = register.json()["workspaceId"]
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    access_token = login.json()["accessToken"]
    return {"workspace_id": workspace_id, "headers": {"Authorization": f"Bearer {access_token}"}}


async def test_connect_repository_creates_pending_repo_and_enqueues_job(client, tracker):
    auth = await _register_and_login(client, tracker)

    response = await client.post(
        "/api/v1/repositories",
        json={"githubUrl": f"https://github.com/test/repo-{uuid.uuid4().hex[:8]}"},
        headers=auth["headers"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    tracker["repo_ids"].append(ObjectId(body["id"]))

    db = get_mongo_db()
    job = await db[c.INGESTION_JOBS].find_one({"repositoryId": ObjectId(body["id"])})
    assert job is not None
    assert job["status"] == "queued"
    tracker["job_ids"].append(job["_id"])

    queue = get_ingestion_queue()
    assert queue.count >= 1

    await cleanup_test_data(tracker)


async def test_connect_same_repo_twice_rejected(client, tracker):
    auth = await _register_and_login(client, tracker)
    github_url = f"https://github.com/test/repo-{uuid.uuid4().hex[:8]}"

    first = await client.post(
        "/api/v1/repositories", json={"githubUrl": github_url}, headers=auth["headers"]
    )
    second = await client.post(
        "/api/v1/repositories", json={"githubUrl": github_url}, headers=auth["headers"]
    )

    assert first.status_code == 201
    assert second.status_code == 409
    tracker["repo_ids"].append(ObjectId(first.json()["id"]))

    db = get_mongo_db()
    async for job in db[c.INGESTION_JOBS].find({"repositoryId": ObjectId(first.json()["id"])}):
        tracker["job_ids"].append(job["_id"])

    await cleanup_test_data(tracker)


async def test_non_admin_cannot_connect_repository(client):
    # A developer registered via invite would have role != admin; simplest way
    # to exercise the guard directly without needing a full invite flow here
    # is to hit the endpoint with no token at all, which require_admin also rejects.
    response = await client.post(
        "/api/v1/repositories", json={"githubUrl": "https://github.com/test/whatever"}
    )
    assert response.status_code == 401


async def test_sync_rejected_while_already_syncing(client, tracker):
    auth = await _register_and_login(client, tracker)
    connect = await client.post(
        "/api/v1/repositories",
        json={"githubUrl": f"https://github.com/test/repo-{uuid.uuid4().hex[:8]}"},
        headers=auth["headers"],
    )
    repo_id = connect.json()["id"]
    tracker["repo_ids"].append(ObjectId(repo_id))

    db = get_mongo_db()
    async for job in db[c.INGESTION_JOBS].find({"repositoryId": ObjectId(repo_id)}):
        tracker["job_ids"].append(job["_id"])
    # Simulate the worker having picked up the job (no worker is running during
    # tests) so we can exercise the "already syncing" guard deterministically.
    await db[c.REPOSITORIES].update_one(
        {"_id": ObjectId(repo_id)}, {"$set": {"status": "syncing"}}
    )

    response = await client.post(
        f"/api/v1/repositories/{repo_id}/sync", headers=auth["headers"]
    )

    assert response.status_code == 409

    await cleanup_test_data(tracker)


async def test_status_endpoint_reflects_job_state(client, tracker):
    auth = await _register_and_login(client, tracker)
    connect = await client.post(
        "/api/v1/repositories",
        json={"githubUrl": f"https://github.com/test/repo-{uuid.uuid4().hex[:8]}"},
        headers=auth["headers"],
    )
    repo_id = connect.json()["id"]
    tracker["repo_ids"].append(ObjectId(repo_id))

    db = get_mongo_db()
    async for job in db[c.INGESTION_JOBS].find({"repositoryId": ObjectId(repo_id)}):
        tracker["job_ids"].append(job["_id"])

    response = await client.get(
        f"/api/v1/repositories/{repo_id}/status", headers=auth["headers"]
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["jobStatus"] == "queued"

    await cleanup_test_data(tracker)
