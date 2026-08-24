import pytest
from fastapi.testclient import TestClient

from app.api import stocks as stocks_api
from app.api import watchlist as watchlist_api
from app.db import SQLiteDatabase, WatchlistRepository
from app.main import app
from app.providers.mock.market_provider import MockMarketProvider
from app.providers.market import MarketProviderError
from app.services.market_service import MarketService
from app.services.watchlist_service import WatchlistService


@pytest.fixture
def client(tmp_path):
    database = SQLiteDatabase(tmp_path / "watchlist.db")
    repository = WatchlistRepository(database)
    market_service = MarketService(provider=MockMarketProvider())
    watchlist_service = WatchlistService(repository, market_service)

    original_watchlist_service = watchlist_api.service
    original_stocks_service = stocks_api.service
    watchlist_api.service = watchlist_service
    stocks_api.service = market_service
    try:
        yield TestClient(app), database
    finally:
        watchlist_api.service = original_watchlist_service
        stocks_api.service = original_stocks_service


def test_search_and_watchlist_crud(client):
    test_client, _database = client

    search = test_client.get("/api/v1/stocks?q=nvidia")
    assert search.status_code == 200
    assert [item["symbol"] for item in search.json()] == ["NVDA"]

    created = test_client.post("/api/v1/watchlist", json={"symbol": "nvda"})
    assert created.status_code == 201
    assert created.json()["symbol"] == "NVDA"
    assert created.json()["data_status"] == "MOCK"

    duplicate = test_client.post("/api/v1/watchlist", json={"symbol": "NVDA"})
    assert duplicate.status_code == 409

    listed = test_client.get("/api/v1/watchlist")
    assert listed.status_code == 200
    assert [item["symbol"] for item in listed.json()] == ["NVDA"]

    assert test_client.delete("/api/v1/watchlist/nvda").status_code == 204
    assert test_client.get("/api/v1/watchlist").json() == []
    assert test_client.delete("/api/v1/watchlist/NVDA").status_code == 404


def test_watchlist_rejects_unknown_symbol(client):
    test_client, _database = client

    response = test_client.post("/api/v1/watchlist", json={"symbol": "UNKNOWN"})
    assert response.status_code == 400


def test_saved_watchlist_survives_quote_provider_failure(client):
    test_client, _database = client
    assert test_client.post(
        "/api/v1/watchlist", json={"symbol": "NVDA"}
    ).status_code == 201

    class FailingProvider:
        def get_quote(self, _symbol):
            raise MarketProviderError("temporary failure")

        def list_quotes(self):
            raise MarketProviderError("temporary failure")

    original_provider = watchlist_api.service.market_service.provider
    watchlist_api.service.market_service.provider = FailingProvider()
    try:
        response = test_client.get("/api/v1/watchlist")
    finally:
        watchlist_api.service.market_service.provider = original_provider

    assert response.status_code == 200
    assert response.json()[0]["symbol"] == "NVDA"
    assert response.json()[0]["data_status"] == "UNAVAILABLE"
    assert response.json()[0]["price"] is None


def test_watchlist_persists_and_uses_created_at_index(client):
    test_client, database = client
    assert test_client.post(
        "/api/v1/watchlist", json={"symbol": "NVDA"}
    ).status_code == 201

    reloaded = WatchlistRepository(SQLiteDatabase(database.path))
    assert [item.symbol for item in reloaded.list()] == ["NVDA"]

    with database.connection() as connection:
        indexes = {
            row["name"]
            for row in connection.execute(
                "PRAGMA index_list('watchlist_items')"
            ).fetchall()
        }
        plan = connection.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT symbol, company_name, currency, created_at
            FROM watchlist_items
            ORDER BY created_at DESC, symbol
            """
        ).fetchall()

    assert "idx_watchlist_items_created_at" in indexes
    assert any(
        "USING INDEX idx_watchlist_items_created_at" in row["detail"]
        for row in plan
    )
