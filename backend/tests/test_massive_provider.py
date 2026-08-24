import httpx
import pytest

from app.providers.market import (
    MarketProviderConfigurationError,
    MarketProviderError,
)
from app.providers.massive import MassiveMarketProvider
from app.schemas.market import DataStatus


class FakeMassiveClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, *, params: dict, timeout: float) -> httpx.Response:
        self.calls.append((url, params))
        if url.endswith("/v3/reference/tickers"):
            payload = {
                "status": "OK",
                "results": [
                    {
                        "ticker": "NVDA",
                        "name": "NVIDIA Corporation",
                        "currency_name": "usd",
                    }
                ],
            }
        elif "/v3/reference/tickers/" in url:
            payload = {
                "status": "OK",
                "results": {
                    "name": "NVIDIA Corporation",
                    "currency_name": "usd",
                },
            }
        else:
            payload = {
                "status": "OK",
                "results": [
                    {"c": 120.0, "t": 1_756_000_000_000},
                    {"c": 126.0, "t": 1_756_086_400_000},
                ],
            }
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )


def test_massive_quote_is_normalized_and_marked_eod():
    client = FakeMassiveClient()
    provider = MassiveMarketProvider(
        api_key="test-key",
        symbols=("NVDA",),
        client=client,
    )

    quote = provider.get_quote("nvda")

    assert quote is not None
    assert quote.symbol == "NVDA"
    assert quote.company_name == "NVIDIA Corporation"
    assert quote.price == 126.0
    assert quote.change_percent == 5.0
    assert quote.currency == "USD"
    assert quote.data_status == DataStatus.EOD
    assert quote.provider == "Massive"
    assert all(call[1]["apiKey"] == "test-key" for call in client.calls)


def test_massive_company_metadata_is_cached():
    client = FakeMassiveClient()
    provider = MassiveMarketProvider(
        api_key="test-key",
        cache_seconds=900,
        client=client,
    )

    first_quote = provider.get_quote("NVDA")
    second_quote = provider.get_quote("NVDA")

    assert first_quote == second_quote
    assert len(client.calls) == 2


def test_massive_searches_active_us_stock_directory():
    client = FakeMassiveClient()
    provider = MassiveMarketProvider(api_key="test-key", client=client)

    results = provider.search_tickers("nvidia", limit=10)

    assert results == [
        {
            "symbol": "NVDA",
            "company_name": "NVIDIA Corporation",
            "currency": "USD",
        }
    ]
    assert client.calls[0][1]["market"] == "stocks"
    assert client.calls[0][1]["active"] == "true"
    assert client.calls[0][1]["search"] == "nvidia"


def test_massive_missing_key_fails_before_http_request():
    client = FakeMassiveClient()
    provider = MassiveMarketProvider(api_key="", client=client)

    with pytest.raises(MarketProviderConfigurationError, match="MASSIVE_API_KEY"):
        provider.get_quote("NVDA")

    assert client.calls == []


class ErrorMassiveClient:
    def get(self, url: str, *, params: dict, timeout: float) -> httpx.Response:
        return httpx.Response(
            403,
            json={"status": "ERROR"},
            request=httpx.Request("GET", url),
        )


def test_massive_http_error_does_not_expose_api_key():
    provider = MassiveMarketProvider(api_key="secret-test-key", client=ErrorMassiveClient())

    with pytest.raises(MarketProviderError) as exc_info:
        provider.get_quote("NVDA")

    assert "secret-test-key" not in str(exc_info.value)
