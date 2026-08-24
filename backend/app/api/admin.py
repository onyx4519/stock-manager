from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_admin
from app.dependencies import admin_repository as repository
from app.schemas.admin import (
    AdminDashboardSummary,
    AdminNotice,
    AdminNoticeCreate,
)
from app.schemas.auth import AuthUser


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardSummary)
def dashboard(
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> AdminDashboardSummary:
    return repository.get_dashboard_summary()


@router.get("/notices", response_model=list[AdminNotice])
def list_notices(
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> list[AdminNotice]:
    return repository.list_notices()


@router.post(
    "/notices",
    response_model=AdminNotice,
    status_code=status.HTTP_201_CREATED,
)
def create_notice(
    payload: AdminNoticeCreate,
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> AdminNotice:
    return repository.create_notice(payload)


@router.delete(
    "/notices/{notice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notice(
    notice_id: int,
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> None:
    if notice_id < 1 or not repository.delete_notice(notice_id):
        raise HTTPException(status_code=404, detail="Published notice not found.")


@router.post(
    "/users/{user_id}/require-password-change",
    status_code=status.HTTP_204_NO_CONTENT,
)
def require_password_change(
    user_id: str,
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> None:
    if not repository.require_password_change(user_id):
        raise HTTPException(status_code=404, detail="Regular account not found.")


@router.post(
    "/users/{user_id}/revoke-sessions",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_sessions(
    user_id: str,
    _admin: Annotated[AuthUser, Depends(get_current_admin)],
) -> None:
    if not repository.revoke_sessions(user_id):
        raise HTTPException(status_code=404, detail="Regular account not found.")
