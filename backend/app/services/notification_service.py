from app.db.notification_repository import NotificationRepository
from app.schemas.notifications import NotificationList


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    def list_notifications(self, user_id: str) -> NotificationList:
        items = self.repository.list_for_user(user_id)
        return NotificationList(
            items=items,
            unread_count=sum(item.read_at is None for item in items),
        )

    def mark_read(self, user_id: str, notification_id: int) -> None:
        if not self.repository.mark_read(user_id, notification_id):
            raise LookupError("Notification not found.")

    def mark_all_read(self, user_id: str) -> None:
        self.repository.mark_all_read(user_id)
