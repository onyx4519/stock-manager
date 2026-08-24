import sqlite3

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import portfolio as portfolio_api
from app.api import transactions as transactions_api
from app.api import watchlist as watchlist_api
from app.db import AuthRepository, SQLiteDatabase, TransactionRepository, WatchlistRepository
from app.main import app
from app.providers.mock.market_provider import MockMarketProvider
from app.services.auth_service import AuthService
from app.services.market_service import MarketService
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
            },
        )
        second = client.post(
            "/api/v1/auth/register",
            json={
                "email": "second@example.com",
                "display_name": "Second User",
                "password": "safe-password-2",
            },
        )
        assert first.status_code == 201
        assert second.status_code == 201
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
    }
    try:
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post("/api/v1/auth/register", json=payload).status_code == 409
        invalid = client.post(
            "/api/v1/auth/login",
            json={"email": payload["email"], "password": "wrong-pass"},
        )
        assert invalid.status_code == 401
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
            json={"confirmed": True, "reason": "MISSING_CONTENT"},
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

        assert feedback["reason"] == "MISSING_CONTENT"
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
    user = repository.create_user(
        email="owner@example.com",
        display_name="Owner",
        password="safe-password",
    )

    records = WatchlistRepository(database).list(user.id)
    assert [record.symbol for record in records] == ["NVDA"]
    with database.connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info('transactions')")
        }
    assert "user_id" in columns
