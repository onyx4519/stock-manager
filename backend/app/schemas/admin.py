from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import AccountDeletionReason, UserRole


class AdminRecentUser(BaseModel):
    id: str
    email: str
    display_name: str
    role: UserRole
    active_sessions: int = 0
    failed_login_attempts: int = 0
    password_change_required: bool = False
    created_at: datetime


class AdminNoticeAudience(StrEnum):
    ALL = "ALL"
    ADMIN = "ADMIN"


class AdminNoticeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    message: str = Field(min_length=2, max_length=500)
    audience: AdminNoticeAudience = AdminNoticeAudience.ALL

    @field_validator("title", "message")
    @classmethod
    def strip_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Notice text must contain at least two characters.")
        return normalized


class AdminNotice(BaseModel):
    id: int
    title: str
    message: str
    audience: AdminNoticeAudience
    created_at: datetime


class AdminDeletionReasonCount(BaseModel):
    reason: AccountDeletionReason
    count: int


class AdminDashboardSummary(BaseModel):
    generated_at: datetime
    total_users: int
    admin_users: int
    regular_users: int
    active_sessions: int
    password_change_required_users: int
    service_notification_users: int
    personalization_users: int
    total_transactions: int
    total_watchlist_items: int
    total_notifications: int
    recent_users: list[AdminRecentUser]
    deletion_reasons: list[AdminDeletionReasonCount]
