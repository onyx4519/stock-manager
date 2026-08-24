import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import admin as admin_api
from app.api import notifications as notifications_api
from app.api import portfolio as portfolio_api
from app.api import transactions as transactions_api
from app.api import watchlist as watchlist_api
from app.db import (
    AdminRepository,
    AuthRepository,
    NotificationRepository,
    SQLiteDatabase,
    TransactionRepository,
    WatchlistRepository,
)
from app.main import app
from app.providers.mock.market_provider import MockMarketProvider
from app.services.auth_service import AuthService
from app.services.market_service import MarketService
from app.services.notification_service import NotificationService
from app.services.portfolio_service import PortfolioService
from app.services.transaction_service import TransactionService
from app.services.watchlist_service import WatchlistService


def test_authentication_and_user_data_isolation(tmp_path):
    database = SQLiteDatabase(tmp_path / "auth.db")
    market_service = MarketService(provider=MockMarketProvider())
    auth_service = AuthService(AuthRepository(database))
    transaction_repository = TransactionRepository(database)
    watchlist_repository = WatchlistRepository(database)

    originals = (
        auth_api.service,
        transactions_api.service,
        portfolio_api.service,
        watchlist_api.service,
    )
    auth_api.service = auth_service
    transactions_api.service = TransactionService(transaction_repository, market_service)
    portfolio_api.service = PortfolioService(transaction_repository, market_service)
    watchlist_api.service = WatchlistService(watchlist_repository, market_service)
    client = TestClient(app)
    try:
        assert client.get("/api/v1/watchlist").status_code == 401

        first = client.post(
            "/api/v1/auth/register",
            json={
                "email": "first@example.com",
                "display_name": "First User",
                "password": "safe-password-1",
                "birth_date": "2000-01-02",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
            },
        )
        second = client.post(
            "/api/v1/auth/register",
            json={
                "email": "second@example.com",
                "display_name": "Second User",
                "password": "safe-password-2",
                "birth_date": "1995-05-15",
                "gender": "FEMALE",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
                "personalization_consent": True,
                "service_notification_consent": True,
            },
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["user"]["birth_date"] == "2000-01-02"
        assert first.json()["user"]["role"] == "USER"
        assert first.json()["user"]["password_change_required"] is False
        assert first.json()["user"]["gender"] == "UNSPECIFIED"
        assert first.json()["user"]["personalization_consent"] is False
        assert first.json()["user"]["personalization_consent_at"] is None
        assert second.json()["user"]["personalization_consent"] is True
        assert second.json()["user"]["gender"] == "FEMALE"
        assert second.json()["user"]["personalization_consent_at"]
        assert first.json()["user"]["service_notification_consent"] is False
        assert second.json()["user"]["service_notification_consent"] is True
        assert second.json()["user"]["service_notification_consent_at"]
        with database.connection() as connection:
            consent_record = connection.execute(
                """
                SELECT account_creation_consent_at,
                       account_creation_consent_version,
                       privacy_collection_consent_at,
                       privacy_collection_consent_version,
                       personalization_consent_version,
                       service_notification_consent_version
                FROM users WHERE id = ?
                """,
                (second.json()["user"]["id"],),
            ).fetchone()
        assert consent_record["account_creation_consent_at"]
        assert (
            consent_record["account_creation_consent_version"]
            == AuthRepository.ACCOUNT_CREATION_CONSENT_VERSION
        )
        assert (
            consent_record["privacy_collection_consent_version"]
            == AuthRepository.PRIVACY_COLLECTION_CONSENT_VERSION
        )
        assert consent_record["privacy_collection_consent_at"]
        assert (
            consent_record["personalization_consent_version"]
            == AuthRepository.PERSONALIZATION_CONSENT_VERSION
        )
        assert (
            consent_record["service_notification_consent_version"]
            == AuthRepository.SERVICE_NOTIFICATION_CONSENT_VERSION
        )
        first_headers = {
            "Authorization": f"Bearer {first.json()['access_token']}"
        }
        second_headers = {
            "Authorization": f"Bearer {second.json()['access_token']}"
        }

        assert client.post(
            "/api/v1/watchlist",
            json={"symbol": "NVDA"},
            headers=first_headers,
        ).status_code == 201
        assert [item["symbol"] for item in client.get(
            "/api/v1/watchlist", headers=first_headers
        ).json()] == ["NVDA"]
        assert client.get(
            "/api/v1/watchlist", headers=second_headers
        ).json() == []

        me = client.get("/api/v1/auth/me", headers=first_headers)
        assert me.status_code == 200
        assert me.json()["email"] == "first@example.com"
        assert me.json()["birth_date"] == "2000-01-02"
        assert me.json()["gender"] == "UNSPECIFIED"
        assert me.json()["personalization_consent"] is False
        preference = client.patch(
            "/api/v1/auth/preferences/notifications",
            json={"service_notification_consent": True},
            headers=first_headers,
        )
        assert preference.status_code == 200
        assert preference.json()["service_notification_consent"] is True
        assert preference.json()["service_notification_consent_at"]
        assert client.post("/api/v1/auth/logout", headers=first_headers).status_code == 204
        assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 401
    finally:
        (
            auth_api.service,
            transactions_api.service,
            portfolio_api.service,
            watchlist_api.service,
        ) = originals


def test_auth_rejects_duplicate_email_and_bad_password(tmp_path):
    database = SQLiteDatabase(tmp_path / "auth-errors.db")
    original = auth_api.service
    auth_api.service = AuthService(AuthRepository(database))
    client = TestClient(app)
    payload = {
        "email": "user@example.com",
        "display_name": "User Name",
        "password": "safe-password",
        "birth_date": "2001-03-04",
        "gender": "MALE",
        "account_creation_consent": True,
        "privacy_collection_consent": True,
    }
    try:
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post("/api/v1/auth/register", json=payload).status_code == 409
        invalid = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "wrong-pass"},
        )
        assert invalid.status_code == 401
        assert invalid.json()["detail"] == {
            "message": "Invalid email or password.",
            "failed_attempts": 1,
        }

        valid = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        assert valid.status_code == 200
        with database.connection() as connection:
            reset = connection.execute(
                """
                SELECT failed_login_attempts, last_failed_login_at
                FROM users WHERE email = ?
                """,
                (payload["email"],),
            ).fetchone()
        assert reset["failed_login_attempts"] == 0
        assert reset["last_failed_login_at"] is None

        unknown = client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@example.com", "password": "wrong-pass"},
        )
        assert unknown.status_code == 401
        assert unknown.json()["detail"]["failed_attempts"] is None
    finally:
        auth_api.service = original


def test_five_failed_logins_require_password_change(tmp_path):
    database = SQLiteDatabase(tmp_path / "forced-password-change.db")
    original = auth_api.service
    auth_api.service = AuthService(AuthRepository(database))
    client = TestClient(app)
    payload = {
        "email": "locked@example.com",
        "display_name": "Locked User",
        "password": "safe-password",
        "birth_date": "2001-03-04",
        "gender": "UNSPECIFIED",
        "account_creation_consent": True,
        "privacy_collection_consent": True,
    }
    try:
        registration = client.post("/api/v1/auth/register", json=payload)
        assert registration.status_code == 201

        for failed_attempts in range(1, 5):
            invalid = client.post(
                "/api/v1/auth/login",
                json={"email": payload["email"], "password": "wrong-pass"},
            )
            assert invalid.status_code == 401
            assert invalid.json()["detail"]["failed_attempts"] == failed_attempts

        with database.connection() as connection:
            before_limit = connection.execute(
                """
                SELECT failed_login_attempts, password_change_required
                FROM users WHERE email = ?
                """,
                (payload["email"],),
            ).fetchone()
        assert before_limit["failed_login_attempts"] == 4
        assert before_limit["password_change_required"] == 0

        fifth_failure = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "wrong-pass"},
        )
        assert fifth_failure.status_code == 401
        assert fifth_failure.json()["detail"]["failed_attempts"] == 5

        with database.connection() as connection:
            at_limit = connection.execute(
                """
                SELECT failed_login_attempts, password_change_required,
                       last_failed_login_at
                FROM users WHERE email = ?
                """,
                (payload["email"],),
            ).fetchone()
        assert at_limit["failed_login_attempts"] == 5
        assert at_limit["password_change_required"] == 1
        assert at_limit["last_failed_login_at"]

        forced_login = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": payload["password"]},
        )
        assert forced_login.status_code == 200
        assert forced_login.json()["user"]["password_change_required"] is True
        forced_headers = {
            "Authorization": f"Bearer {forced_login.json()['access_token']}"
        }
        assert client.get("/api/v1/auth/me", headers=forced_headers).status_code == 200
        blocked = client.patch(
            "/api/v1/auth/preferences/notifications",
            json={"service_notification_consent": True},
            headers=forced_headers,
        )
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == "Password change required."

        changed = client.patch(
            "/api/v1/auth/password",
            json={
                "current_password": payload["password"],
                "new_password": "new-safe-password",
            },
            headers=forced_headers,
        )
        assert changed.status_code == 204
        assert client.get("/api/v1/auth/me", headers=forced_headers).status_code == 401

        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "new-safe-password"},
        )
        assert new_login.status_code == 200
        assert new_login.json()["user"]["password_change_required"] is False
        with database.connection() as connection:
            reset = connection.execute(
                """
                SELECT failed_login_attempts, password_change_required,
                       last_failed_login_at
                FROM users WHERE email = ?
                """,
                (payload["email"],),
            ).fetchone()
        assert reset["failed_login_attempts"] == 0
        assert reset["password_change_required"] == 0
        assert reset["last_failed_login_at"] is None
    finally:
        auth_api.service = original


def test_admin_account_creation_and_server_side_permission_check(tmp_path):
    database = SQLiteDatabase(tmp_path / "admin-auth.db")
    auth_service = AuthService(AuthRepository(database))
    original = auth_api.service
    auth_api.service = auth_service
    client = TestClient(app)
    try:
        admin = auth_service.create_admin(
            email="admin@example.com",
            display_name="System Admin",
            password="strong-admin-password",
        )
        assert admin.role == "ADMIN"

        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "strong-admin-password",
            },
        )
        assert admin_login.status_code == 200
        assert admin_login.json()["user"]["role"] == "ADMIN"
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }
        assert client.get(
            "/api/v1/auth/admin/me", headers=admin_headers
        ).status_code == 200

        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": "regular@example.com",
                "display_name": "Regular User",
                "password": "safe-password",
                "birth_date": "2000-01-01",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
                "role": "ADMIN",
            },
        )
        assert registration.status_code == 201
        assert registration.json()["user"]["role"] == "USER"
        regular_headers = {
            "Authorization": f"Bearer {registration.json()['access_token']}"
        }
        assert client.get(
            "/api/v1/auth/admin/me", headers=regular_headers
        ).status_code == 403

        with pytest.raises(ValueError):
            auth_service.create_admin(
                email="weak@example.com",
                display_name="Weak Admin",
                password="too-short",
            )
    finally:
        auth_api.service = original


def test_admin_dashboard_is_private_and_returns_service_summary(tmp_path):
    database = SQLiteDatabase(tmp_path / "admin-dashboard.db")
    auth_service = AuthService(AuthRepository(database))
    originals = (auth_api.service, admin_api.repository)
    auth_api.service = auth_service
    admin_api.repository = AdminRepository(database)
    client = TestClient(app)
    try:
        auth_service.create_admin(
            email="dashboard-admin@example.com",
            display_name="Dashboard Admin",
            password="strong-admin-password",
        )
        regular = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dashboard-user@example.com",
                "display_name": "Dashboard User",
                "password": "safe-password",
                "birth_date": "2000-01-01",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
                "personalization_consent": True,
                "service_notification_consent": True,
            },
        )
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "dashboard-admin@example.com",
                "password": "strong-admin-password",
            },
        )
        assert regular.status_code == 201
        assert admin_login.status_code == 200
        regular_user_id = regular.json()["user"]["id"]
        regular_headers = {
            "Authorization": f"Bearer {regular.json()['access_token']}"
        }
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        with database.connection() as connection:
            now = "2026-08-25T00:00:00+00:00"
            connection.execute(
                """
                INSERT INTO transactions (
                  user_id, symbol, transaction_type, quantity, price, currency,
                  fee, tax, executed_at, created_at, updated_at
                ) VALUES (?, 'NVDA', 'BUY', '1', '100', 'USD', '0', '0', ?, ?, ?)
                """,
                (regular_user_id, now, now, now),
            )
            connection.execute(
                """
                INSERT INTO watchlist_items (
                  user_id, symbol, company_name, currency, created_at
                ) VALUES (?, 'NVDA', 'NVIDIA Corporation', 'USD', ?)
                """,
                (regular_user_id, now),
            )
            connection.execute(
                """
                INSERT INTO account_deletion_feedback (reason, created_at)
                VALUES ('DATA_QUALITY', ?)
                """,
                (now,),
            )

        assert client.get(
            "/api/v1/admin/dashboard",
            headers=regular_headers,
        ).status_code == 403
        dashboard = client.get(
            "/api/v1/admin/dashboard",
            headers=admin_headers,
        )
        assert dashboard.status_code == 200
        payload = dashboard.json()
        assert payload["total_users"] == 2
        assert payload["admin_users"] == 1
        assert payload["regular_users"] == 1
        assert payload["active_sessions"] == 2
        assert payload["service_notification_users"] == 1
        assert payload["personalization_users"] == 1
        assert payload["total_transactions"] == 1
        assert payload["total_watchlist_items"] == 1
        assert payload["total_notifications"] == 1
        assert len(payload["recent_users"]) == 2
        assert payload["deletion_reasons"] == [
            {"reason": "DATA_QUALITY", "count": 1}
        ]
        assert "password_hash" not in payload["recent_users"][0]
    finally:
        auth_api.service, admin_api.repository = originals


def test_admin_can_publish_notices_and_manage_regular_user_security(tmp_path):
    database = SQLiteDatabase(tmp_path / "admin-operations.db")
    notification_repository = NotificationRepository(database)
    auth_service = AuthService(AuthRepository(database), notification_repository)
    originals = (
        auth_api.service,
        admin_api.repository,
        notifications_api.service,
    )
    auth_api.service = auth_service
    admin_api.repository = AdminRepository(database)
    notifications_api.service = NotificationService(notification_repository)
    client = TestClient(app)
    try:
        admin = auth_service.create_admin(
            email="operations-admin@example.com",
            display_name="Operations Admin",
            password="strong-admin-password",
        )
        regular = client.post(
            "/api/v1/auth/register",
            json={
                "email": "operations-user@example.com",
                "display_name": "Operations User",
                "password": "safe-password",
                "birth_date": "2000-01-01",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
            },
        )
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "operations-admin@example.com",
                "password": "strong-admin-password",
            },
        )
        regular_headers = {
            "Authorization": f"Bearer {regular.json()['access_token']}"
        }
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }
        regular_user_id = regular.json()["user"]["id"]

        assert client.post(
            "/api/v1/admin/notices",
            json={"title": "금지", "message": "일반 사용자는 발행할 수 없습니다."},
            headers=regular_headers,
        ).status_code == 403
        public_notice = client.post(
            "/api/v1/admin/notices",
            json={
                "title": "서비스 점검 안내",
                "message": "오늘 오후 서비스 점검이 예정되어 있습니다.",
                "audience": "ALL",
            },
            headers=admin_headers,
        )
        private_notice = client.post(
            "/api/v1/admin/notices",
            json={
                "title": "관리자 운영 안내",
                "message": "관리자만 확인하는 운영 공지입니다.",
                "audience": "ADMIN",
            },
            headers=admin_headers,
        )
        assert public_notice.status_code == 201
        assert private_notice.status_code == 201
        notices = client.get(
            "/api/v1/admin/notices", headers=admin_headers
        )
        assert notices.status_code == 200
        assert [item["audience"] for item in notices.json()] == ["ADMIN", "ALL"]

        assert client.delete(
            f"/api/v1/admin/notices/{public_notice.json()['id']}",
            headers=regular_headers,
        ).status_code == 403
        with database.connection() as connection:
            system_notice_id = connection.execute(
                """
                SELECT id FROM notifications
                WHERE notification_key = 'system:notification-center-launched'
                """
            ).fetchone()["id"]
        assert client.delete(
            f"/api/v1/admin/notices/{system_notice_id}",
            headers=admin_headers,
        ).status_code == 404

        regular_notifications = client.get(
            "/api/v1/notifications", headers=regular_headers
        )
        regular_titles = {
            item["title"] for item in regular_notifications.json()["items"]
        }
        assert "서비스 점검 안내" in regular_titles
        assert "관리자 운영 안내" not in regular_titles

        assert client.delete(
            f"/api/v1/admin/notices/{public_notice.json()['id']}",
            headers=admin_headers,
        ).status_code == 204
        assert [
            item["title"]
            for item in client.get(
                "/api/v1/admin/notices", headers=admin_headers
            ).json()
        ] == ["관리자 운영 안내"]

        force_change = client.post(
            f"/api/v1/admin/users/{regular_user_id}/require-password-change",
            headers=admin_headers,
        )
        assert force_change.status_code == 204
        assert client.get(
            "/api/v1/auth/me", headers=regular_headers
        ).status_code == 401
        relogin = client.post(
            "/api/v1/auth/login",
            json={
                "email": "operations-user@example.com",
                "password": "safe-password",
            },
        )
        assert relogin.json()["user"]["password_change_required"] is True
        relogin_headers = {
            "Authorization": f"Bearer {relogin.json()['access_token']}"
        }
        assert client.post(
            f"/api/v1/admin/users/{regular_user_id}/revoke-sessions",
            headers=admin_headers,
        ).status_code == 204
        assert client.get(
            "/api/v1/auth/me", headers=relogin_headers
        ).status_code == 401
        assert client.post(
            f"/api/v1/admin/users/{admin.id}/require-password-change",
            headers=admin_headers,
        ).status_code == 404
    finally:
        (
            auth_api.service,
            admin_api.repository,
            notifications_api.service,
        ) = originals


def test_password_change_verifies_current_password_and_revokes_sessions(tmp_path):
    database = SQLiteDatabase(tmp_path / "password-change.db")
    auth_service = AuthService(AuthRepository(database))
    original = auth_api.service
    auth_api.service = auth_service
    client = TestClient(app)
    try:
        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": "password@example.com",
                "display_name": "Password User",
                "password": "safe-password",
                "birth_date": "2000-01-01",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
            },
        )
        assert registration.status_code == 201
        first_headers = {
            "Authorization": f"Bearer {registration.json()['access_token']}"
        }
        second_login = client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "safe-password"},
        )
        second_headers = {
            "Authorization": f"Bearer {second_login.json()['access_token']}"
        }

        wrong_current = client.patch(
            "/api/v1/auth/password",
            json={
                "current_password": "wrong-password",
                "new_password": "new-pass",
            },
            headers=first_headers,
        )
        assert wrong_current.status_code == 400
        assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 200

        changed = client.patch(
            "/api/v1/auth/password",
            json={
                "current_password": "safe-password",
                "new_password": "new-pass",
            },
            headers=first_headers,
        )
        assert changed.status_code == 204
        assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 401
        assert client.get("/api/v1/auth/me", headers=second_headers).status_code == 401
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "safe-password"},
        ).status_code == 401
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "password@example.com", "password": "new-pass"},
        ).status_code == 200

        auth_service.create_admin(
            email="password-admin@example.com",
            display_name="Password Admin",
            password="strong-admin-password",
        )
        admin_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "password-admin@example.com",
                "password": "strong-admin-password",
            },
        )
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }
        weak_admin_password = client.patch(
            "/api/v1/auth/password",
            json={
                "current_password": "strong-admin-password",
                "new_password": "new-pass",
            },
            headers=admin_headers,
        )
        assert weak_admin_password.status_code == 400
        assert client.get("/api/v1/auth/me", headers=admin_headers).status_code == 200
    finally:
        auth_api.service = original


def test_auth_rejects_invalid_basic_profile_values(tmp_path):
    database = SQLiteDatabase(tmp_path / "auth-profile-errors.db")
    original = auth_api.service
    auth_api.service = AuthService(AuthRepository(database))
    client = TestClient(app)
    base_payload = {
        "email": "profile@example.com",
        "display_name": "Profile User",
        "password": "safe-password",
        "birth_date": "2000-01-01",
        "gender": "UNSPECIFIED",
        "account_creation_consent": True,
        "privacy_collection_consent": True,
    }
    try:
        missing_birth_date = dict(base_payload)
        missing_birth_date.pop("birth_date")
        assert client.post(
            "/api/v1/auth/register", json=missing_birth_date
        ).status_code == 422

        future_birth_date = {**base_payload, "birth_date": "2999-01-01"}
        assert client.post(
            "/api/v1/auth/register", json=future_birth_date
        ).status_code == 422

        invalid_gender = {**base_payload, "gender": "OTHER"}
        assert client.post(
            "/api/v1/auth/register", json=invalid_gender
        ).status_code == 422

        missing_consent = dict(base_payload)
        missing_consent.pop("account_creation_consent")
        assert client.post(
            "/api/v1/auth/register", json=missing_consent
        ).status_code == 422

        declined_consent = {**base_payload, "account_creation_consent": False}
        assert client.post(
            "/api/v1/auth/register", json=declined_consent
        ).status_code == 422

        missing_privacy = dict(base_payload)
        missing_privacy.pop("privacy_collection_consent")
        assert client.post(
            "/api/v1/auth/register", json=missing_privacy
        ).status_code == 422

        declined_privacy = {**base_payload, "privacy_collection_consent": False}
        assert client.post(
            "/api/v1/auth/register", json=declined_privacy
        ).status_code == 422
    finally:
        auth_api.service = original


def test_account_deletion_requires_confirmation_and_keeps_only_anonymous_reason(
    tmp_path,
):
    database = SQLiteDatabase(tmp_path / "account-deletion.db")
    original = auth_api.service
    auth_api.service = AuthService(AuthRepository(database))
    client = TestClient(app)
    try:
        registration = client.post(
            "/api/v1/auth/register",
            json={
                "email": "leaving@example.com",
                "display_name": "Leaving User",
                "password": "safe-password",
                "birth_date": "1999-12-31",
                "gender": "UNSPECIFIED",
                "account_creation_consent": True,
                "privacy_collection_consent": True,
            },
        )
        assert registration.status_code == 201
        session = registration.json()
        user_id = session["user"]["id"]
        headers = {"Authorization": f"Bearer {session['access_token']}"}

        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO transactions (
                  user_id, symbol, transaction_type, quantity, price, currency,
                  fee, tax, executed_at, created_at, updated_at
                ) VALUES (?, 'NVDA', 'BUY', '1', '100', 'USD', '0', '0', ?, ?, ?)
                """,
                (
                    user_id,
                    "2026-08-25T00:00:00+00:00",
                    "2026-08-25T00:00:00+00:00",
                    "2026-08-25T00:00:00+00:00",
                ),
            )
            connection.execute(
                """
                INSERT INTO watchlist_items (
                  user_id, symbol, company_name, currency, created_at
                ) VALUES (?, 'NVDA', 'NVIDIA Corporation', 'USD', ?)
                """,
                (user_id, "2026-08-25T00:00:00+00:00"),
            )

        not_confirmed = client.request(
            "DELETE",
            "/api/v1/auth/account",
            json={"confirmed": False, "reason": "MISSING_CONTENT"},
            headers=headers,
        )
        assert not_confirmed.status_code == 422
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

        deleted = client.request(
            "DELETE",
            "/api/v1/auth/account",
            json={"confirmed": True, "reason": "NO_REASON"},
            headers=headers,
        )
        assert deleted.status_code == 204
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401

        with database.connection() as connection:
            assert connection.execute(
                "SELECT COUNT(*) FROM users WHERE id = ?", (user_id,)
            ).fetchone()[0] == 0
            assert connection.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = ?", (user_id,)
            ).fetchone()[0] == 0
            assert connection.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)
            ).fetchone()[0] == 0
            assert connection.execute(
                "SELECT COUNT(*) FROM watchlist_items WHERE user_id = ?", (user_id,)
            ).fetchone()[0] == 0
            feedback = connection.execute(
                "SELECT reason, created_at FROM account_deletion_feedback"
            ).fetchone()
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info('account_deletion_feedback')"
                )
            }

        assert feedback["reason"] == "NO_REASON"
        assert feedback["created_at"]
        assert "user_id" not in columns
        assert "email" not in columns
    finally:
        auth_api.service = original


def test_legacy_records_are_preserved_and_claimed_by_first_user(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE transactions (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT NOT NULL,
              transaction_type TEXT NOT NULL,
              quantity TEXT NOT NULL,
              price TEXT NOT NULL,
              currency TEXT NOT NULL,
              fee TEXT NOT NULL,
              tax TEXT NOT NULL,
              executed_at TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE watchlist_items (
              symbol TEXT PRIMARY KEY,
              company_name TEXT NOT NULL,
              currency TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            INSERT INTO watchlist_items VALUES (
              'NVDA', 'NVIDIA Corporation', 'USD', '2026-08-20T00:00:00Z'
            );
            """
        )

    database = SQLiteDatabase(path)
    repository = AuthRepository(database)
    admin = AuthService(repository).create_admin(
        email="admin-owner@example.com",
        display_name="Admin Owner",
        password="strong-admin-password",
    )
    user = repository.create_user(
        email="owner@example.com",
        display_name="Owner",
        password="safe-password",
    )

    records = WatchlistRepository(database).list(user.id)
    admin_records = WatchlistRepository(database).list(admin.id)
    assert [record.symbol for record in records] == ["NVDA"]
    assert admin_records == []
    with database.connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info('transactions')")
        }
    assert "user_id" in columns


def test_existing_users_receive_safe_profile_and_consent_defaults(tmp_path):
    path = tmp_path / "existing-users.db"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
              id TEXT PRIMARY KEY,
              email TEXT NOT NULL COLLATE NOCASE UNIQUE,
              display_name TEXT NOT NULL,
              password_hash TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            INSERT INTO users VALUES (
              'existing-user', 'existing@example.com', 'Existing User',
              '!test', '2026-08-20T00:00:00Z'
            );
            CREATE TABLE notifications (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              notification_key TEXT NOT NULL UNIQUE,
              user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
              category TEXT NOT NULL CHECK(category IN ('NOTICE', 'ACCOUNT', 'SERVICE')),
              title TEXT NOT NULL,
              message TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            INSERT INTO notifications (
              notification_key, user_id, category, title, message, created_at
            ) VALUES (
              'system:notification-center-launched', NULL, 'NOTICE',
              '내부 알림센터가 준비되었습니다', '테스트 공지',
              '2026-08-25T00:00:00+09:00'
            );
            CREATE TABLE account_deletion_feedback (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              reason TEXT NOT NULL CHECK(reason IN (
                'MISSING_CONTENT',
                'DIFFICULT_TO_USE',
                'DATA_QUALITY',
                'PRIVACY_CONCERN',
                'NO_LONGER_NEEDED'
              )),
              created_at TEXT NOT NULL
            );
            INSERT INTO account_deletion_feedback (reason, created_at)
            VALUES ('DATA_QUALITY', '2026-08-20T00:00:00Z');
            """
        )

    database = SQLiteDatabase(path)
    database.initialize()
    with database.connection() as connection:
        row = connection.execute(
            """
            SELECT birth_date, gender, role,
                   failed_login_attempts, password_change_required,
                   last_failed_login_at,
                   account_creation_consent_at,
                   account_creation_consent_version,
                   privacy_collection_consent_at,
                   privacy_collection_consent_version,
                   personalization_consent, personalization_consent_at,
                   personalization_consent_version,
                   service_notification_consent,
                   service_notification_consent_at,
                   service_notification_consent_version
            FROM users WHERE id = 'existing-user'
            """
        ).fetchone()
        feedback = connection.execute(
            "SELECT reason FROM account_deletion_feedback ORDER BY id"
        ).fetchall()
        notification = connection.execute(
            """
            SELECT audience FROM notifications
            WHERE notification_key = 'system:notification-center-launched'
            """
        ).fetchone()
        connection.execute(
            """
            INSERT INTO account_deletion_feedback (reason, created_at)
            VALUES ('NO_REASON', '2026-08-25T00:00:00Z')
            """
        )

    assert row["birth_date"] is None
    assert row["gender"] == "UNSPECIFIED"
    assert row["role"] == "USER"
    assert notification["audience"] == "ADMIN"
    assert row["failed_login_attempts"] == 0
    assert row["password_change_required"] == 0
    assert row["last_failed_login_at"] is None
    assert row["account_creation_consent_at"] is None
    assert row["account_creation_consent_version"] is None
    assert row["privacy_collection_consent_at"] is None
    assert row["privacy_collection_consent_version"] is None
    assert row["personalization_consent"] == 0
    assert row["personalization_consent_at"] is None
    assert row["personalization_consent_version"] is None
    assert row["service_notification_consent"] == 0
    assert row["service_notification_consent_at"] is None
    assert row["service_notification_consent_version"] is None
    assert [item["reason"] for item in feedback] == ["DATA_QUALITY"]
