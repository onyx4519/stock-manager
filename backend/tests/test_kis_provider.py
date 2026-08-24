import httpx
import pytest

from app.providers.kis import KisMarketProvider
from app.providers.market import (
    MarketProviderConfigurationError,
    MarketProviderError,
)
from app.schemas.market import DataStatus


class FakeKisClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict,
        json: dict,
        timeout: float,
    ) -> httpx.Response:
        self.calls.append(("POST", url, json))
        return httpx.Response(
            200,
            json={"access_token": "test-token", "expires_in": 86400},
            request=httpx.Request("POST", url),
        )

    def get(
        self,
        url: str,
        *,
        headers: dict,
        params: dict,
        timeout: float,
    ) -> httpx.Response:
        self.calls.append(("GET", url, params))
        return httpx.Response(
            200,
            json={
                "rt_cd": "0",
                "output1": {"hts_kor_isnm": "삼성전자"},
                "output2": [
                    {"stck_bsop_date": "20260821", "stck_clpr": "81000"},
                    {"stck_bsop_date": "20260820", "stck_clpr": "80000"},
                ],
            },
            request=httpx.Request("GET", url),
        )


def test_kis_quote_is_normalized_and_marked_eod():
    client = FakeKisClient()
    provider = KisMarketProvider(
        app_key="test-key",
        app_secret="test-secret",
        symbols=("005930",),
        client=client,
    )

    quote = provider.get_quote("005930")

    assert quote is not None
    assert quote.symbol == "005930"
    assert quote.company_name == "삼성전자"
    assert quote.price == 81000
    assert quote.change_percent == 1.25
    assert quote.currency == "KRW"
    assert quote.data_status == DataStatus.EOD
    assert quote.provider == "KIS"
    assert quote.timestamp.isoformat() == "2026-08-21T15:30:00+09:00"


def test_kis_token_and_quote_are_cached():
    client = FakeKisClient()
    provider = KisMarketProvider(
        app_key="test-key",
        app_secret="test-secret",
        cache_seconds=900,
        client=client,
    )

    first_quote = provider.get_quote("005930")
    second_quote = provider.get_quote("005930")

    assert first_quote == second_quote
    assert [call[0] for call in client.calls] == ["POST", "GET"]


def test_kis_rejects_non_domestic_symbol_before_http_request():
    client = FakeKisClient()
    provider = KisMarketProvider(
        app_key="test-key",
        app_secret="test-secret",
        client=client,
    )

    assert provider.get_quote("NVDA") is None
    assert client.calls == []


def test_kis_missing_credentials_fail_before_http_request():
    client = FakeKisClient()
    provider = KisMarketProvider(app_key="", app_secret="", client=client)

    with pytest.raises(MarketProviderConfigurationError, match="KIS_APP_KEY"):
        provider.get_quote("005930")

    assert client.calls == []


class ErrorKisClient(FakeKisClient):
    def post(
        self,
        url: str,
        *,
        headers: dict,
        json: dict,
        timeout: float,
    ) -> httpx.Response:
        return httpx.Response(
            403,
            json={"error": "invalid_client"},
            request=httpx.Request("POST", url),
        )


def test_kis_http_error_does_not_expose_credentials():
    provider = KisMarketProvider(
        app_key="secret-app-key",
        app_secret="secret-app-secret",
        client=ErrorKisClient(),
    )

    with pytest.raises(MarketProviderError) as exc_info:
        provider.get_quote("005930")

    message = str(exc_info.value)
    assert "secret-app-key" not in message
    assert "secret-app-secret" not in message
