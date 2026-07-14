from fastapi import APIRouter, Depends, status

from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.learning_paths import service
from app.modules.learning_paths.schemas import (
    CompleteModuleResponse,
    GeneratePathRequest,
    LearningModuleResponse,
    LearningPathResponse,
)

router = APIRouter(prefix="/learning-paths", tags=["learning-paths"])


@router.post("/generate", response_model=LearningPathResponse, status_code=status.HTTP_201_CREATED)
async def generate(
    body: GeneratePathRequest, current_user: CurrentUser = Depends(get_current_user)
):
    """Manual trigger/backstop — normally generation happens automatically on
    invite-based registration; this exists for the case where that automatic
    attempt failed (e.g. the assigned repo wasn't finished syncing yet)."""
    return await service.generate_learning_path(developer_profile_id=body.developer_profile_id)


@router.get("/me", response_model=LearningPathResponse)
async def get_my_path(current_user: CurrentUser = Depends(get_current_user)):
    return await service.get_learning_path(user_id=current_user.user_id)


@router.get("/{path_id}/modules", response_model=list[LearningModuleResponse])
async def get_modules(path_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.list_modules(path_id=path_id)


@router.post("/modules/{module_id}/complete", response_model=CompleteModuleResponse)
async def complete(module_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.complete_module(module_id=module_id, user_id=current_user.user_id)
