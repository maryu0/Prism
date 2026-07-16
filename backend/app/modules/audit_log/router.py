from fastapi import APIRouter, Depends

from app.modules.audit_log import service
from app.modules.audit_log.schemas import AuditLogResponse
from app.modules.auth.deps import CurrentUser, require_admin

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("", response_model=AuditLogResponse)
async def get_audit_log(current_user: CurrentUser = Depends(require_admin)):
    return await service.list_audit_log(workspace_id=current_user.workspace_id)
