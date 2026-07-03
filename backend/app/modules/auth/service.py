from datetime import timedelta

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_mongo_db, get_redis_client
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    verify_password,
)
from app.models import collections as c
from app.models.common import utcnow

REFRESH_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
INVITE_TOKEN_TTL_HOURS = 72
LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 10 * 60


async def register_admin(*, email: str, password: str, name: str) -> dict:
    db = get_mongo_db()
    if await db[c.USERS].find_one({"email": email}):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")

    workspace_id = ObjectId()
    user_id = ObjectId()

    await db[c.WORKSPACES].insert_one(
        {
            "_id": workspace_id,
            "name": f"{name}'s Workspace",
            "ownerId": user_id,
            "inviteTokens": [],
        }
    )
    await db[c.USERS].insert_one(
        {
            "_id": user_id,
            "email": email,
            "passwordHash": hash_password(password),
            "name": name,
            "role": "admin",
            "workspaceId": workspace_id,
            "createdAt": utcnow(),
            "lastLoginAt": None,
        }
    )
    return {"userId": str(user_id), "workspaceId": str(workspace_id)}


async def register_via_invite(*, email: str, password: str, name: str, invite_token: str) -> dict:
    db = get_mongo_db()
    workspace = await db[c.WORKSPACES].find_one({"inviteTokens.token": invite_token})
    invite = None
    if workspace:
        invite = next(
            (t for t in workspace["inviteTokens"] if t["token"] == invite_token), None
        )

    if (
        not workspace
        or invite is None
        or invite["used"]
        or invite["expiresAt"] < utcnow()
        or invite["email"] != email
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This invite is no longer valid — ask your admin to resend it.",
        )

    if await db[c.USERS].find_one({"email": email}):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use")

    user_id = ObjectId()
    await db[c.USERS].insert_one(
        {
            "_id": user_id,
            "email": email,
            "passwordHash": hash_password(password),
            "name": name,
            "role": invite["role"],
            "workspaceId": workspace["_id"],
            "createdAt": utcnow(),
            "lastLoginAt": None,
        }
    )
    await db[c.WORKSPACES].update_one(
        {"_id": workspace["_id"], "inviteTokens.token": invite_token},
        {"$set": {"inviteTokens.$.used": True}},
    )
    return {
        "userId": str(user_id),
        "workspaceId": str(workspace["_id"]),
        "role": invite["role"],
        "assignedRepositoryId": str(invite["assignedRepositoryId"]),
    }


async def login(*, email: str, password: str) -> dict:
    db = get_mongo_db()
    redis = get_redis_client()
    attempts_key = f"login_attempts:{email}"

    attempts = await redis.get(attempts_key)
    if attempts is not None and int(attempts) >= LOGIN_ATTEMPT_LIMIT:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many failed attempts. Try again later."
        )

    user = await db[c.USERS].find_one({"email": email})
    if not user or not verify_password(password, user["passwordHash"]):
        pipe = redis.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, LOGIN_ATTEMPT_WINDOW_SECONDS)
        await pipe.execute()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect")

    await redis.delete(attempts_key)
    await db[c.USERS].update_one({"_id": user["_id"]}, {"$set": {"lastLoginAt": utcnow()}})

    access_token = create_access_token(
        user_id=str(user["_id"]), workspace_id=str(user["workspaceId"]), role=user["role"]
    )
    refresh_token = await _issue_refresh_token(str(user["_id"]))
    return {"accessToken": access_token, "refreshToken": refresh_token}


async def _issue_refresh_token(user_id: str) -> str:
    redis = get_redis_client()
    token = generate_opaque_token()
    await redis.set(f"refresh:{token}", user_id, ex=REFRESH_TOKEN_TTL_SECONDS)
    return token


async def refresh_access_token(*, refresh_token: str) -> dict:
    redis = get_redis_client()
    user_id = await redis.get(f"refresh:{refresh_token}")
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please log in again")

    # Rotation: the old token is single-use — burn it before issuing a new one.
    await redis.delete(f"refresh:{refresh_token}")

    db = get_mongo_db()
    user = await db[c.USERS].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please log in again")

    access_token = create_access_token(
        user_id=str(user["_id"]), workspace_id=str(user["workspaceId"]), role=user["role"]
    )
    new_refresh_token = await _issue_refresh_token(user_id)
    return {"accessToken": access_token, "refreshToken": new_refresh_token}


async def logout(*, refresh_token: str | None) -> None:
    if refresh_token:
        redis = get_redis_client()
        await redis.delete(f"refresh:{refresh_token}")


async def create_invite(
    *, workspace_id: str, email: str, role: str, assigned_repository_id: str
) -> dict:
    db = get_mongo_db()

    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(assigned_repository_id), "workspaceId": ObjectId(workspace_id)}
    )
    if not repo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "assignedRepositoryId does not exist in this workspace"
        )
    if repo["status"] != "ready":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Repository is not ready yet — wait for sync to finish"
        )

    existing_member = await db[c.USERS].find_one(
        {"email": email, "workspaceId": ObjectId(workspace_id)}
    )
    if existing_member:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "This email is already a member of the workspace"
        )

    token = generate_opaque_token()
    expires_at = utcnow() + timedelta(hours=INVITE_TOKEN_TTL_HOURS)

    await db[c.WORKSPACES].update_one(
        {"_id": ObjectId(workspace_id)},
        {
            "$push": {
                "inviteTokens": {
                    "token": token,
                    "email": email,
                    "role": role,
                    "assignedRepositoryId": ObjectId(assigned_repository_id),
                    "expiresAt": expires_at,
                    "used": False,
                }
            }
        },
    )
    return {"token": token, "expiresAt": expires_at}
