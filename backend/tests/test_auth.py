import uuid

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.database import get_mongo_db, get_redis_client
from app.main import app
from app.models import collections as c

# Our @lru_cache'd Motor/Redis clients are created once and bound to whichever
# event loop exists at that moment. pytest-asyncio's default is a fresh loop per
# test function, which would kill the cached client after the first test. Pinning
# every test in this module to the same ("session") loop keeps it alive for the
# whole run — this is the supported mechanism, not the deprecated custom
# event_loop fixture override.
pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def tracker():
    """Plain (non-async) fixture — just hands back empty lists for a test to
    record what it created. Deliberately NOT an async-generator fixture with
    teardown logic: that pattern turned out to run unreliably here once test
    functions were pinned to a session-scoped loop (teardown silently no-op'd
    with no error). Calling cleanup_test_data() explicitly at the end of each
    test is more code per test, but it's guaranteed to actually run."""
    return {"emails": [], "repo_ids": []}


async def cleanup_test_data(tracker: dict) -> None:
    db = get_mongo_db()
    emails = tracker["emails"]
    repo_ids = tracker["repo_ids"]

    if emails:
        users = await db[c.USERS].find({"email": {"$in": emails}}).to_list(length=None)
        owner_ids = [u["_id"] for u in users]
        await db[c.USERS].delete_many({"email": {"$in": emails}})
        if owner_ids:
            await db[c.WORKSPACES].delete_many({"ownerId": {"$in": owner_ids}})
        redis = get_redis_client()
        for email in emails:
            await redis.delete(f"login_attempts:{email}")

    if repo_ids:
        await db[c.REPOSITORIES].delete_many({"_id": {"$in": repo_ids}})


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.prism"


async def test_register_admin_creates_workspace_and_user(client, tracker):
    email = unique_email("admin")
    tracker["emails"].append(email)

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Test Admin"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "userId" in body
    assert "workspaceId" in body

    db = get_mongo_db()
    user = await db[c.USERS].find_one({"email": email})
    assert user["role"] == "admin"

    await cleanup_test_data(tracker)


async def test_register_duplicate_email_rejected(client, tracker):
    email = unique_email("dup")
    tracker["emails"].append(email)
    payload = {"email": email, "password": "testpass123", "name": "Dup"}

    first = await client.post("/api/v1/auth/register", json=payload)
    second = await client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409

    await cleanup_test_data(tracker)


async def test_login_wrong_password_rejected(client, tracker):
    email = unique_email("login")
    tracker["emails"].append(email)
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correctpass", "name": "Login Test"},
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrongpass"}
    )

    assert response.status_code == 401

    await cleanup_test_data(tracker)


async def test_login_then_me_roundtrip(client, tracker):
    email = unique_email("me")
    tracker["emails"].append(email)
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Me Test"},
    )

    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    access_token = login.json()["accessToken"]

    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert me.status_code == 200
    assert me.json()["email"] == email

    await cleanup_test_data(tracker)


async def test_me_without_token_rejected(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_includes_assigned_repository_id(client, tracker):
    admin_email = unique_email("me-repo-admin")
    tracker["emails"].append(admin_email)
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "testpass123", "name": "Me Repo Admin"},
    )
    workspace_id = register.json()["workspaceId"]
    login = await client.post(
        "/api/v1/auth/login", json={"email": admin_email, "password": "testpass123"}
    )
    admin_headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    # Admin has no DeveloperProfile — assignedRepositoryId must be null, not missing/erroring.
    admin_me = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert admin_me.status_code == 200
    assert admin_me.json()["assignedRepositoryId"] is None

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(workspace_id),
            "githubUrl": "https://github.com/test/me-repo",
            "defaultBranch": "main",
            "accessTokenEnc": "test",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )

    invitee_email = unique_email("me-repo-dev")
    tracker["emails"].append(invitee_email)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invite",
        json={
            "email": invitee_email,
            "role": "developer",
            "assignedRepositoryId": str(repo_id),
        },
        headers=admin_headers,
    )
    invite_token = invite.json()["inviteUrl"].split("invite=")[1]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": invitee_email,
            "password": "devpass123",
            "name": "Me Repo Dev",
            "inviteToken": invite_token,
            "experienceLevel": "mid",
        },
    )
    dev_login = await client.post(
        "/api/v1/auth/login", json={"email": invitee_email, "password": "devpass123"}
    )
    dev_headers = {"Authorization": f"Bearer {dev_login.json()['accessToken']}"}

    dev_me = await client.get("/api/v1/auth/me", headers=dev_headers)
    assert dev_me.status_code == 200
    assert dev_me.json()["assignedRepositoryId"] == str(repo_id)

    await db[c.DEVELOPER_PROFILES].delete_many({"assignedRepositoryId": repo_id})
    path = await db[c.LEARNING_PATHS].find_one({"repositoryId": repo_id})
    if path:
        await db[c.LEARNING_MODULES].delete_many({"pathId": path["_id"]})
        await db[c.LEARNING_PATHS].delete_one({"_id": path["_id"]})

    await cleanup_test_data(tracker)


async def test_refresh_token_rotates_and_old_token_dies(client, tracker):
    email = unique_email("refresh")
    tracker["emails"].append(email)
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123", "name": "Refresh Test"},
    )
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpass123"}
    )
    old_cookie = login.cookies.get("refresh_token")
    client.cookies.set("refresh_token", old_cookie)

    first_refresh = await client.post("/api/v1/auth/refresh")
    assert first_refresh.status_code == 200

    client.cookies.set("refresh_token", old_cookie)
    reuse_attempt = await client.post("/api/v1/auth/refresh")
    assert reuse_attempt.status_code == 401

    await cleanup_test_data(tracker)


async def test_invite_requires_ready_repository(client, tracker):
    admin_email = unique_email("inviter")
    tracker["emails"].append(admin_email)

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "testpass123", "name": "Inviter"},
    )
    workspace_id = register.json()["workspaceId"]
    login = await client.post(
        "/api/v1/auth/login", json={"email": admin_email, "password": "testpass123"}
    )
    access_token = login.json()["accessToken"]
    headers = {"Authorization": f"Bearer {access_token}"}

    invitee_email = unique_email("invitee")
    tracker["emails"].append(invitee_email)

    missing_repo_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invite",
        json={
            "email": invitee_email,
            "role": "developer",
            "assignedRepositoryId": str(ObjectId()),
        },
        headers=headers,
    )
    assert missing_repo_response.status_code == 400

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(workspace_id),
            "githubUrl": "https://github.com/test/repo",
            "defaultBranch": "main",
            "accessTokenEnc": "test",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )

    ok_response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invite",
        json={
            "email": invitee_email,
            "role": "developer",
            "assignedRepositoryId": str(repo_id),
        },
        headers=headers,
    )
    assert ok_response.status_code == 201
    assert "inviteUrl" in ok_response.json()

    await cleanup_test_data(tracker)


async def test_register_via_invite_assigns_role_and_repo_not_self_reported(client, tracker):
    admin_email = unique_email("admin2")
    tracker["emails"].append(admin_email)

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": "testpass123", "name": "Admin2"},
    )
    workspace_id = register.json()["workspaceId"]
    login = await client.post(
        "/api/v1/auth/login", json={"email": admin_email, "password": "testpass123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['accessToken']}"}

    db = get_mongo_db()
    repo_id = ObjectId()
    tracker["repo_ids"].append(repo_id)
    await db[c.REPOSITORIES].insert_one(
        {
            "_id": repo_id,
            "workspaceId": ObjectId(workspace_id),
            "githubUrl": "https://github.com/test/repo2",
            "defaultBranch": "main",
            "accessTokenEnc": "test",
            "status": "ready",
            "languageStats": {},
            "locCount": 0,
        }
    )

    invitee_email = unique_email("dev")
    tracker["emails"].append(invitee_email)
    invite = await client.post(
        f"/api/v1/workspaces/{workspace_id}/invite",
        json={
            "email": invitee_email,
            "role": "developer",
            "assignedRepositoryId": str(repo_id),
        },
        headers=headers,
    )
    invite_token = invite.json()["inviteUrl"].split("invite=")[1]

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": invitee_email,
            "password": "devpass123",
            "name": "New Dev",
            "inviteToken": invite_token,
            "experienceLevel": "mid",
        },
    )

    assert register_response.status_code == 201
    body = register_response.json()
    assert body["role"] == "developer"
    assert body["assignedRepositoryId"] == str(repo_id)

    # Reusing the same invite token must fail — single use.
    reuse = await client.post(
        "/api/v1/auth/register",
        json={
            "email": invitee_email,
            "password": "devpass123",
            "name": "New Dev",
            "inviteToken": invite_token,
            "experienceLevel": "mid",
        },
    )
    assert reuse.status_code == 400

    db = get_mongo_db()
    await db[c.DEVELOPER_PROFILES].delete_many({"assignedRepositoryId": repo_id})
    path = await db[c.LEARNING_PATHS].find_one({"repositoryId": repo_id})
    if path:
        await db[c.LEARNING_MODULES].delete_many({"pathId": path["_id"]})
        await db[c.LEARNING_PATHS].delete_one({"_id": path["_id"]})

    await cleanup_test_data(tracker)
