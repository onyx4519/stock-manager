from fastapi.testclient import TestClient

from app.api import market as market_api
from app.api.dart import get_dart_provider
from app.api.news import get_news_provider
from app.main import app
from app.providers.dart import DartAPIError, DartConfigurationError
from app.providers.market import MarketProviderConfigurationError
from app.providers.mock.market_provider import MockMarketProvider
from app.providers.news import NewsProviderConfigurationError

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

    def search_disclosures(self, corp_code, *, days, limit):
        assert corp_code == "00126380"
        return 1, [
            {
                "corporation_class": "Y",
                "corporation_name": "삼성전자",
                "corporation_code": corp_code,
                "stock_code": "005930",
                "report_name": "반기보고서 (2026.06)",
                "receipt_number": "20260814001234",
                "filer_name": "삼성전자",
                "receipt_date": "2026-08-14",
                "remarks": "연",
                "viewer_url": (
                    "https://dart.fss.or.kr/dsaf001/main.do?"
                    "rcpNo=20260814001234"
                ),
            }
        ][:limit]

    def get_major_accounts(self, corp_code, *, business_year, report_code):
        assert corp_code == "00126380"
        return "CFS", [
            {
                "receipt_number": "20260318001234",
                "business_year": str(business_year),
                "report_code": report_code,
                "account_name": "매출액",
                "financial_statement_division": "CFS",
                "financial_statement_name": "연결재무제표",
                "statement_division": "IS",
                "statement_name": "손익계산서",
                "current_term_name": "제57기",
                "current_term_date": "2025.01.01 ~ 2025.12.31",
                "current_term_amount": 300000,
                "current_term_cumulative_amount": None,
                "previous_term_name": "제56기",
                "previous_term_date": "2024.01.01 ~ 2024.12.31",
                "previous_term_amount": 250000,
                "currency": "KRW",
            }
        ]


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


def test_dart_disclosures_and_financials():
    app.dependency_overrides[get_dart_provider] = StubDartProvider
    try:
        disclosures = client.get(
            "/api/v1/dart/companies/005930/disclosures?days=365&limit=10"
        )
        financials = client.get(
            "/api/v1/dart/companies/005930/financials?"
            "business_year=2025&report_code=11011"
        )
    finally:
        app.dependency_overrides.clear()

    assert disclosures.status_code == 200
    assert disclosures.json()["total_count"] == 1
    assert disclosures.json()["items"][0]["receipt_number"] == "20260814001234"
    assert financials.status_code == 200
    assert financials.json()["financial_statement_division"] == "CFS"
    assert financials.json()["accounts"][0]["current_term_amount"] == 300000


class StubNewsProvider:
    symbols = ("NVDA", "AAPL")

    def list_news(self, *, symbol=None, limit=20):
        ticker = symbol.upper() if symbol else "NVDA"
        return [
            {
                "id": "test-news-1",
                "title": "NVIDIA announces quarterly results",
                "author": "Reporter",
                "description": "Results summary.",
                "article_url": "https://example.com/news/1",
                "image_url": None,
                "publisher_name": "Example Finance",
                "publisher_homepage_url": "https://example.com",
                "published_at": "2026-08-24T12:30:00Z",
                "tickers": [ticker],
                "provider": "Massive",
            }
        ][:limit]


class UnconfiguredNewsProvider:
    symbols = ("NVDA",)

    def list_news(self, *, symbol=None, limit=20):
        raise NewsProviderConfigurationError("MASSIVE_API_KEY is not configured.")


def test_news_endpoint_returns_normalized_feed():
    app.dependency_overrides[get_news_provider] = StubNewsProvider
    try:
        response = client.get("/api/v1/news?symbol=nvda&limit=10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["symbols"] == ["NVDA"]
    assert response.json()["total_count"] == 1
    assert response.json()["items"][0]["publisher_name"] == "Example Finance"


def test_news_endpoint_reports_missing_configuration():
    app.dependency_overrides[get_news_provider] = UnconfiguredNewsProvider
    try:
        response = client.get("/api/v1/news?symbol=NVDA")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "MASSIVE_API_KEY is not configured."
