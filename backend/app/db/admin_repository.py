from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.admin import (
    AdminDashboardSummary,
    AdminDeletionReasonCount,
    AdminRecentUser,
)


class AdminRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def get_dashboard_summary(self) -> AdminDashboardSummary:
        now = datetime.now(timezone.utc)
        with self.database.connection() as connection:
            user_counts = connection.execute(
                """
                SELECT
                  COUNT(*) AS total_users,
                  SUM(CASE WHEN role = 'ADMIN' THEN 1 ELSE 0 END) AS admin_users,
                  SUM(CASE WHEN role = 'USER' THEN 1 ELSE 0 END) AS regular_users,
                  SUM(password_change_required) AS password_change_required_users,
                  SUM(service_notification_consent) AS service_notification_users,
                  SUM(personalization_consent) AS personalization_users
                FROM users
                WHERE id != ?
                """,
                (self.database.LEGACY_USER_ID,),
            ).fetchone()
            active_sessions = connection.execute(
                """
                SELECT COUNT(*) FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.expires_at > ? AND users.id != ?
                """,
                (now.isoformat(), self.database.LEGACY_USER_ID),
            ).fetchone()[0]
            total_transactions = connection.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id != ?",
                (self.database.LEGACY_USER_ID,),
            ).fetchone()[0]
            total_watchlist_items = connection.execute(
                "SELECT COUNT(*) FROM watchlist_items WHERE user_id != ?",
                (self.database.LEGACY_USER_ID,),
            ).fetchone()[0]
            total_notifications = connection.execute(
                "SELECT COUNT(*) FROM notifications"
            ).fetchone()[0]
            recent_users = connection.execute(
                """
                SELECT id, email, display_name, role, created_at
                FROM users
                WHERE id != ?
                ORDER BY created_at DESC, id DESC
                LIMIT 8
                """,
                (self.database.LEGACY_USER_ID,),
            ).fetchall()
            deletion_reasons = connection.execute(
                """
                SELECT reason, COUNT(*) AS count
                FROM account_deletion_feedback
                GROUP BY reason
                ORDER BY count DESC, reason
                """
            ).fetchall()

        return AdminDashboardSummary(
            generated_at=now,
            total_users=int(user_counts["total_users"] or 0),
            admin_users=int(user_counts["admin_users"] or 0),
            regular_users=int(user_counts["regular_users"] or 0),
            active_sessions=int(active_sessions),
            password_change_required_users=int(
                user_counts["password_change_required_users"] or 0
            ),
            service_notification_users=int(
                user_counts["service_notification_users"] or 0
            ),
            personalization_users=int(user_counts["personalization_users"] or 0),
            total_transactions=int(total_transactions),
            total_watchlist_items=int(total_watchlist_items),
            total_notifications=int(total_notifications),
            recent_users=[
                AdminRecentUser.model_validate(dict(row)) for row in recent_users
            ],
            deletion_reasons=[
                AdminDeletionReasonCount.model_validate(dict(row))
                for row in deletion_reasons
            ],
        )
