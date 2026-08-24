from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api import portfolio as portfolio_api
from app.api import transactions as transactions_api
from app.db import SQLiteDatabase, TransactionRepository
from app.main import app
from app.providers.mock.market_provider import MockMarketProvider
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.transaction_service import TransactionService


@pytest.fixture
def client(tmp_path):
    database = SQLiteDatabase(tmp_path / "transactions.db")
    repository = TransactionRepository(database)
    market_service = MarketService(provider=MockMarketProvider())
    transaction_service = TransactionService(repository, market_service)
    portfolio_service = PortfolioService(repository, market_service)

    original_transaction_service = transactions_api.service
    original_portfolio_service = portfolio_api.service
    transactions_api.service = transaction_service
    portfolio_api.service = portfolio_service
    try:
        yield TestClient(app), database
    finally:
        transactions_api.service = original_transaction_service
        portfolio_api.service = original_portfolio_service


def payload(
    *,
    transaction_type: str = "BUY",
    quantity: str = "10",
    price: str = "100",
    fee: str = "2",
    tax: str = "0",
) -> dict:
    return {
        "symbol": "NVDA",
        "transaction_type": transaction_type,
        "quantity": quantity,
        "price": price,
        "currency": "USD",
        "fee": fee,
        "tax": tax,
        "executed_at": "2026-08-20T10:00:00+09:00",
    }


def test_transaction_crud_and_portfolio_calculation(client):
    test_client, _database = client
    buy_response = test_client.post("/api/v1/transactions", json=payload())
    assert buy_response.status_code == 201
    buy = buy_response.json()

    sell_response = test_client.post(
        "/api/v1/transactions",
        json=payload(
            transaction_type="SELL",
            quantity="3",
            price="130",
            fee="1",
            tax="1",
        ),
    )
    assert sell_response.status_code == 201
    sell = sell_response.json()

    list_response = test_client.get("/api/v1/transactions")
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [sell["id"], buy["id"]]

    position_response = test_client.get("/api/v1/portfolio/positions")
    assert position_response.status_code == 200
    position = position_response.json()[0]
    assert Decimal(str(position["quantity"])) == Decimal("7")
    assert Decimal(str(position["average_cost"])) == Decimal("100.2")
    assert Decimal(str(position["market_value"])) == Decimal("843.5")
    assert Decimal(str(position["realized_pnl"])) == Decimal("87.4")
    assert Decimal(str(position["unrealized_pnl"])) == Decimal("142.1")

    summary_response = test_client.get("/api/v1/portfolio/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["positions_count"] == 1
    assert summary["currencies"][0]["currency"] == "USD"

    update_response = test_client.patch(
        f"/api/v1/transactions/{buy['id']}",
        json={"price": "110"},
    )
    assert update_response.status_code == 200
    assert Decimal(str(update_response.json()["price"])) == Decimal("110")

    blocked_delete = test_client.delete(f"/api/v1/transactions/{buy['id']}")
    assert blocked_delete.status_code == 409

    assert test_client.delete(f"/api/v1/transactions/{sell['id']}").status_code == 204
    assert test_client.delete(f"/api/v1/transactions/{buy['id']}").status_code == 204
    assert test_client.get("/api/v1/transactions").json() == []


def test_transaction_rejects_oversell_and_wrong_currency(client):
    test_client, _database = client

    oversell = test_client.post(
        "/api/v1/transactions",
        json=payload(transaction_type="SELL", quantity="1"),
    )
    assert oversell.status_code == 409

    wrong_currency = payload()
    wrong_currency["currency"] = "KRW"
    response = test_client.post("/api/v1/transactions", json=wrong_currency)
    assert response.status_code == 400
    assert "USD" in response.json()["detail"]


def test_sqlite_transactions_persist_and_use_symbol_index(client):
    test_client, database = client
    assert test_client.post("/api/v1/transactions", json=payload()).status_code == 201

    reloaded_repository = TransactionRepository(SQLiteDatabase(database.path))
    assert len(reloaded_repository.list(symbol="NVDA")) == 1

    with database.connection() as connection:
        indexes = {
            row["name"]
            for row in connection.execute("PRAGMA index_list('transactions')").fetchall()
        }
        plan = connection.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM transactions
            WHERE symbol = ?
            ORDER BY executed_at DESC, id DESC
            """,
            ("NVDA",),
        ).fetchall()

    assert "idx_transactions_symbol_executed_at" in indexes
    assert any("USING INDEX idx_transactions_symbol_executed_at" in row["detail"] for row in plan)
