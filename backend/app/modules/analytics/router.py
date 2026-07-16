from fastapi import APIRouter, Depends

from app.modules.analytics import service
from app.modules.analytics.schemas import (
    KnowledgeGapsResponse,
    MyProgressResponse,
    TeamProgressResponse,
)
from app.modules.auth.deps import CurrentUser, get_current_user, require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/me", response_model=MyProgressResponse)
async def get_my_progress(current_user: CurrentUser = Depends(get_current_user)):
    return await service.get_my_progress(user_id=current_user.user_id)


@router.get("/team", response_model=TeamProgressResponse)
async def get_team_progress(current_user: CurrentUser = Depends(require_admin)):
    return await service.get_team_progress(workspace_id=current_user.workspace_id)


@router.get("/knowledge-gaps", response_model=KnowledgeGapsResponse)
async def get_knowledge_gaps(current_user: CurrentUser = Depends(require_admin)):
    return await service.get_knowledge_gaps(workspace_id=current_user.workspace_id)
