from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import notifications as notifications_api
from app.db import AuthRepository, NotificationRepository, SQLiteDatabase
from app.main import app
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService


def register(client: TestClient, email: str):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Notification User",
            "password": "safe-password",
            "birth_date": "2000-01-01",
            "gender": "UNSPECIFIED",
            "account_creation_consent": True,
            "privacy_collection_consent": True,
            "service_notification_consent": True,
        },
    )


def test_notification_center_read_state_and_user_isolation(tmp_path):
    database = SQLiteDatabase(tmp_path / "notifications.db")
    notification_repository = NotificationRepository(database)
    auth_service = AuthService(AuthRepository(database), notification_repository)
    notification_service = NotificationService(notification_repository)
    originals = (auth_api.service, notifications_api.service)
    auth_api.service = auth_service
    notifications_api.service = notification_service
    client = TestClient(app)

    try:
        assert client.get("/api/v1/notifications").status_code == 401

        first = register(client, "first-notification@example.com")
        second = register(client, "second-notification@example.com")
        assert first.status_code == 201
        assert second.status_code == 201
        first_headers = {
            "Authorization": f"Bearer {first.json()['access_token']}"
        }
        second_headers = {
            "Authorization": f"Bearer {second.json()['access_token']}"
        }

        first_list = client.get(
            "/api/v1/notifications", headers=first_headers
        )
        assert first_list.status_code == 200
        assert first_list.json()["unread_count"] == 2
        assert {item["title"] for item in first_list.json()["items"]} == {
            "가입이 완료되었습니다",
            "내부 알림센터가 준비되었습니다",
        }

        welcome_id = next(
            item["id"]
            for item in first_list.json()["items"]
            if item["title"] == "가입이 완료되었습니다"
        )
        assert client.patch(
            f"/api/v1/notifications/{welcome_id}/read",
            headers=second_headers,
        ).status_code == 404
        assert client.patch(
            f"/api/v1/notifications/{welcome_id}/read",
            headers=first_headers,
        ).status_code == 204
        assert client.get(
            "/api/v1/notifications", headers=first_headers
        ).json()["unread_count"] == 1

        assert client.patch(
            "/api/v1/notifications/read-all", headers=first_headers
        ).status_code == 204
        assert client.get(
            "/api/v1/notifications", headers=first_headers
        ).json()["unread_count"] == 0
        assert client.get(
            "/api/v1/notifications", headers=second_headers
        ).json()["unread_count"] == 2
    finally:
        auth_api.service, notifications_api.service = originals
