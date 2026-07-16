from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.core.database import get_mongo_db
from app.models import collections as c
from app.modules.auth import service
from app.modules.auth.deps import CurrentUser, get_current_user, require_admin
from app.modules.auth.schemas import (
    AccessTokenResponse,
    InviteRequest,
    InviteResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
)

router = APIRouter(tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="strict",
        max_age=service.REFRESH_TOKEN_TTL_SECONDS,
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    if body.invite_token:
        if body.experience_level is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "experienceLevel is required when registering via invite",
            )
        return await service.register_via_invite(
            email=body.email,
            password=body.password,
            name=body.name,
            invite_token=body.invite_token,
            experience_level=body.experience_level,
        )
    return await service.register_admin(email=body.email, password=body.password, name=body.name)


@router.post("/auth/login", response_model=AccessTokenResponse)
async def login(body: LoginRequest, response: Response):
    tokens = await service.login(email=body.email, password=body.password)
    _set_refresh_cookie(response, tokens["refreshToken"])
    return {"accessToken": tokens["accessToken"]}


@router.post("/auth/refresh", response_model=AccessTokenResponse)
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No refresh token")
    tokens = await service.refresh_access_token(refresh_token=refresh_token)
    _set_refresh_cookie(response, tokens["refreshToken"])
    return {"accessToken": tokens["accessToken"]}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    await service.logout(refresh_token=refresh_token)
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.get("/auth/me", response_model=MeResponse)
async def me(current_user: CurrentUser = Depends(get_current_user)):
    db = get_mongo_db()
    user = await db[c.USERS].find_one({"_id": ObjectId(current_user.user_id)})
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    assigned_repository_id = None
    profile = await db[c.DEVELOPER_PROFILES].find_one({"userId": user["_id"]})
    if profile:
        assigned_repository_id = str(profile["assignedRepositoryId"])

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "workspaceId": str(user["workspaceId"]),
        "assignedRepositoryId": assigned_repository_id,
    }


@router.post(
    "/workspaces/{workspace_id}/invite",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite(
    workspace_id: str,
    body: InviteRequest,
    current_user: CurrentUser = Depends(require_admin),
):
    if workspace_id != current_user.workspace_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot invite to another workspace")
    result = await service.create_invite(
        workspace_id=workspace_id,
        actor_id=current_user.user_id,
        email=body.email,
        role=body.role,
        assigned_repository_id=body.assigned_repository_id,
    )
    settings = get_settings()
    invite_url = f"{settings.frontend_origin}/signup?invite={result['token']}"
    return {"inviteUrl": invite_url, "expiresAt": result["expiresAt"]}
