from fastapi import APIRouter, Depends, Query

from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.search import service
from app.modules.search.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search_code(
    q: str = Query(..., min_length=1, description="Natural-language search query"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
):
    results = await service.search_workspace_code(
        workspace_id=current_user.workspace_id, query=q, limit=limit
    )
    return results
