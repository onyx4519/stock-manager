from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.dependencies import notification_service as service
from app.schemas.auth import AuthUser
from app.schemas.notifications import NotificationList


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def list_notifications(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> NotificationList:
    return service.list_notifications(user.id)


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> None:
    service.mark_all_read(user.id)


@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    notification_id: int,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> None:
    try:
        service.mark_read(user.id, notification_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        ) from exc
