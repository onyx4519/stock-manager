from fastapi.testclient import TestClient

from app.api import market as market_api
from app.api.dart import get_dart_provider
from app.main import app
from app.providers.dart import DartAPIError, DartConfigurationError
from app.providers.market import MarketProviderConfigurationError
from app.providers.mock.market_provider import MockMarketProvider

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["mock_mode"] is (data["market_provider"] == "mock")


def test_quote_is_marked_mock():
    original_provider = market_api.service.provider
    market_api.service.provider = MockMarketProvider()
    try:
        response = client.get("/api/v1/market/quotes/NVDA")
    finally:
        market_api.service.provider = original_provider

    assert response.status_code == 200
    assert response.json()["data_status"] == "MOCK"


class UnconfiguredMarketProvider:
    def get_quote(self, symbol: str):
        raise MarketProviderConfigurationError("MASSIVE_API_KEY is not configured.")

    def list_quotes(self):
        raise MarketProviderConfigurationError("MASSIVE_API_KEY is not configured.")


def test_market_provider_configuration_error_is_sanitized():
    original_provider = market_api.service.provider
    market_api.service.provider = UnconfiguredMarketProvider()
    try:
        response = client.get("/api/v1/market/quotes/NVDA")
    finally:
        market_api.service.provider = original_provider

    assert response.status_code == 503
    assert response.json()["detail"] == "Market data provider is not configured."


class StubDartProvider:
    def find_company(self, *, corp_name=None, stock_code=None):
        if stock_code == "005930" or corp_name == "삼성전자":
            return {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "corp_eng_name": "SAMSUNG ELECTRONICS CO.,LTD",
                "stock_code": "005930",
                "modify_date": "20260101",
            }
        return None


class UnconfiguredDartProvider:
    def find_company(self, *, corp_name=None, stock_code=None):
        raise DartConfigurationError("DART_API_KEY is not configured.")


class FailingDartProvider:
    def find_company(self, *, corp_name=None, stock_code=None):
        raise DartAPIError("OpenDART test failure.")


def test_dart_company_search():
    app.dependency_overrides[get_dart_provider] = StubDartProvider
    try:
        response = client.get("/api/v1/dart/companies/search?stock_code=005930")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["corp_name"] == "삼성전자"
    assert response.json()["stock_code"] == "005930"


def test_dart_company_search_requires_filter():
    response = client.get("/api/v1/dart/companies/search")
    assert response.status_code == 422


def test_dart_company_search_reports_missing_configuration():
    app.dependency_overrides[get_dart_provider] = UnconfiguredDartProvider
    try:
        response = client.get("/api/v1/dart/companies/search?stock_code=005930")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "DART_API_KEY is not configured."


def test_dart_company_search_hides_upstream_error_details():
    app.dependency_overrides[get_dart_provider] = FailingDartProvider
    try:
        response = client.get("/api/v1/dart/companies/search?stock_code=005930")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "OpenDART is unavailable or returned invalid data."
    )
