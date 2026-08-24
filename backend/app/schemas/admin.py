from datetime import datetime

from pydantic import BaseModel

from app.schemas.auth import AccountDeletionReason, UserRole


class AdminRecentUser(BaseModel):
    id: str
    email: str
    display_name: str
    role: UserRole
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
