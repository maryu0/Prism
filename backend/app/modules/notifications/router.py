from fastapi import APIRouter, Depends

from app.modules.auth.deps import CurrentUser, get_current_user
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationListResponse, NotificationResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(current_user: CurrentUser = Depends(get_current_user)):
    return await service.list_notifications(user_id=current_user.user_id)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(notification_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.mark_notification_read(
        notification_id=notification_id, user_id=current_user.user_id
    )
