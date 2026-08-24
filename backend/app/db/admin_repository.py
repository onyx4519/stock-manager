import uuid
from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.admin import (
    AdminDashboardSummary,
    AdminDeletionReasonCount,
    AdminNotice,
    AdminNoticeCreate,
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
                SELECT users.id, users.email, users.display_name, users.role,
                       users.failed_login_attempts,
                       users.password_change_required,
                       users.created_at,
                       COUNT(sessions.token_hash) AS active_sessions
                FROM users
                LEFT JOIN sessions
                  ON sessions.user_id = users.id
                 AND sessions.expires_at > ?
                WHERE users.id != ?
                GROUP BY users.id
                ORDER BY users.created_at DESC, users.id DESC
                LIMIT 8
                """,
                (now.isoformat(), self.database.LEGACY_USER_ID),
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

    def create_notice(self, payload: AdminNoticeCreate) -> AdminNotice:
        created_at = datetime.now(timezone.utc).isoformat()
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO notifications (
                  notification_key, user_id, audience, category,
                  title, message, created_at
                ) VALUES (?, NULL, ?, 'NOTICE', ?, ?, ?)
                """,
                (
                    f"admin:notice:{uuid.uuid4()}",
                    payload.audience.value,
                    payload.title,
                    payload.message,
                    created_at,
                ),
            )
            row = connection.execute(
                """
                SELECT id, title, message, audience, created_at
                FROM notifications WHERE id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        if row is None:
            raise RuntimeError("Created notice could not be loaded.")
        return AdminNotice.model_validate(dict(row))

    def list_notices(self, limit: int = 20) -> list[AdminNotice]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, title, message, audience, created_at
                FROM notifications
                WHERE notification_key LIKE 'admin:notice:%'
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [AdminNotice.model_validate(dict(row)) for row in rows]

    def delete_notice(self, notice_id: int) -> bool:
        with self.database.connection() as connection:
            result = connection.execute(
                """
                DELETE FROM notifications
                WHERE id = ? AND notification_key LIKE 'admin:notice:%'
                """,
                (notice_id,),
            )
        return result.rowcount == 1

    def require_password_change(self, user_id: str) -> bool:
        with self.database.connection() as connection:
            result = connection.execute(
                """
                UPDATE users
                SET password_change_required = 1
                WHERE id = ? AND id != ? AND role = 'USER'
                """,
                (user_id, self.database.LEGACY_USER_ID),
            )
            if result.rowcount == 1:
                connection.execute(
                    "DELETE FROM sessions WHERE user_id = ?",
                    (user_id,),
                )
        return result.rowcount == 1

    def revoke_sessions(self, user_id: str) -> bool:
        with self.database.connection() as connection:
            target = connection.execute(
                """
                SELECT 1 FROM users
                WHERE id = ? AND id != ? AND role = 'USER'
                """,
                (user_id, self.database.LEGACY_USER_ID),
            ).fetchone()
            if target is None:
                return False
            connection.execute(
                "DELETE FROM sessions WHERE user_id = ?",
                (user_id,),
            )
        return True
