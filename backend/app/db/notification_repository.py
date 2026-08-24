from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.notifications import NotificationCategory, NotificationItem


class NotificationRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def list_for_user(self, user_id: str) -> list[NotificationItem]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT notifications.id, notifications.category,
                       notifications.title, notifications.message,
                       notifications.created_at, notification_reads.read_at
                FROM notifications
                LEFT JOIN notification_reads
                  ON notification_reads.notification_id = notifications.id
                 AND notification_reads.user_id = ?
                WHERE notifications.user_id IS NULL
                   OR notifications.user_id = ?
                ORDER BY notifications.created_at DESC, notifications.id DESC
                """,
                (user_id, user_id),
            ).fetchall()
        return [NotificationItem.model_validate(dict(row)) for row in rows]

    def create_for_user(
        self,
        *,
        user_id: str,
        notification_key: str,
        category: NotificationCategory,
        title: str,
        message: str,
    ) -> None:
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO notifications (
                  notification_key, user_id, category, title, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    notification_key,
                    user_id,
                    category.value,
                    title,
                    message,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def mark_read(self, user_id: str, notification_id: int) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connection() as connection:
            visible = connection.execute(
                """
                SELECT 1 FROM notifications
                WHERE id = ? AND (user_id IS NULL OR user_id = ?)
                """,
                (notification_id, user_id),
            ).fetchone()
            if visible is None:
                return False
            connection.execute(
                """
                INSERT INTO notification_reads (notification_id, user_id, read_at)
                VALUES (?, ?, ?)
                ON CONFLICT(notification_id, user_id)
                DO UPDATE SET read_at = excluded.read_at
                """,
                (notification_id, user_id, now),
            )
        return True

    def mark_all_read(self, user_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO notification_reads (notification_id, user_id, read_at)
                SELECT id, ?, ?
                FROM notifications
                WHERE user_id IS NULL OR user_id = ?
                ON CONFLICT(notification_id, user_id)
                DO UPDATE SET read_at = excluded.read_at
                """,
                (user_id, now, user_id),
            )
