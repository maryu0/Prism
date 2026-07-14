from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_mongo_db
from app.models import collections as c
from app.modules.auth.deps import CurrentUser, get_current_user, require_admin
from app.modules.graph.schemas import FileComponentsResponse, RepositoryGraphResponse
from app.modules.graph.service import get_file_components, get_repository_graph
from app.modules.repositories import service
from app.modules.repositories.schemas import (
    ConnectRepositoryRequest,
    RepositoryResponse,
    RepositoryStatusResponse,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def connect_repository(
    body: ConnectRepositoryRequest, current_user: CurrentUser = Depends(require_admin)
):
    result = await service.connect_repository(
        workspace_id=current_user.workspace_id,
        github_url=body.github_url,
        access_token=body.access_token,
        default_branch=body.default_branch,
    )
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one({"_id": ObjectId(result["id"])})
    return _to_response(repo)


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(current_user: CurrentUser = Depends(get_current_user)):
    db = get_mongo_db()
    cursor = db[c.REPOSITORIES].find({"workspaceId": ObjectId(current_user.workspace_id)})
    return [_to_response(repo) async for repo in cursor]


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    db = get_mongo_db()
    repo = await db[c.REPOSITORIES].find_one(
        {"_id": ObjectId(repository_id), "workspaceId": ObjectId(current_user.workspace_id)}
    )
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")
    return _to_response(repo)


@router.get("/{repository_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(
    repository_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    result = await service.get_status(
        repository_id=repository_id, workspace_id=current_user.workspace_id
    )
    return result


@router.get("/{repository_id}/graph", response_model=RepositoryGraphResponse)
async def get_graph(
    repository_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    return await get_repository_graph(
        repository_id=repository_id, workspace_id=current_user.workspace_id
    )


@router.get("/{repository_id}/graph/file-components", response_model=FileComponentsResponse)
async def get_graph_file_components(
    repository_id: str,
    file_id: str = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await get_file_components(
        repository_id=repository_id, workspace_id=current_user.workspace_id, file_id=file_id
    )


@router.post("/{repository_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_repository(
    repository_id: str, current_user: CurrentUser = Depends(require_admin)
):
    return await service.trigger_sync(
        repository_id=repository_id, workspace_id=current_user.workspace_id
    )


def _to_response(repo: dict) -> dict:
    return {
        "id": str(repo["_id"]),
        "githubUrl": repo["githubUrl"],
        "defaultBranch": repo["defaultBranch"],
        "status": repo["status"],
        "lastSyncedAt": repo.get("lastSyncedAt"),
        "languageStats": repo.get("languageStats", {}),
        "locCount": repo.get("locCount", 0),
    }
