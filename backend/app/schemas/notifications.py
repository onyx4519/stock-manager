from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class NotificationCategory(StrEnum):
    NOTICE = "NOTICE"
    ACCOUNT = "ACCOUNT"
    SERVICE = "SERVICE"


class NotificationItem(BaseModel):
    id: int
    category: NotificationCategory
    title: str
    message: str
    created_at: datetime
    read_at: datetime | None = None


class NotificationList(BaseModel):
    items: list[NotificationItem]
    unread_count: int
