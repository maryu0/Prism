from fastapi import APIRouter, Depends

from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.chat import service
from app.modules.chat.schemas import AskRequest, AskResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, current_user: CurrentUser = Depends(get_current_user)):
    result = await service.ask_question(
        workspace_id=current_user.workspace_id, question=body.question
    )
    return result
