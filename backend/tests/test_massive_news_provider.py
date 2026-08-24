import httpx
import pytest

from app.providers.massive import MassiveNewsProvider
from app.providers.news import (
    NewsProviderConfigurationError,
    NewsProviderDataError,
    NewsProviderError,
)


class FakeMassiveNewsClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, *, params: dict, timeout: float) -> httpx.Response:
        self.calls.append((url, params))
        ticker = params["ticker"]
        payload = {
            "status": "OK",
            "results": [
                {
                    "id": f"article-{ticker}",
                    "publisher": {
                        "name": "Example Finance",
                        "homepage_url": "https://example.com",
                    },
                    "title": f"{ticker} reports quarterly results",
                    "author": "Reporter",
                    "published_utc": "2026-08-24T12:30:00Z",
                    "article_url": f"https://example.com/{ticker.lower()}",
                    "tickers": [ticker],
                    "description": "Quarterly results summary.",
                }
            ],
        }
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )


def test_massive_news_is_normalized_sorted_and_cached():
    client = FakeMassiveNewsClient()
    provider = MassiveNewsProvider(
        api_key="test-key",
        symbols=("NVDA", "AAPL"),
        cache_seconds=900,
        client=client,
    )

    first = provider.list_news(limit=10)
    second = provider.list_news(limit=10)

    assert len(first) == 2
    assert first[0].publisher_name == "Example Finance"
    assert first[0].published_at.isoformat() == "2026-08-24T12:30:00+00:00"
    assert first[0].provider == "Massive"
    assert first == second
    assert len(client.calls) == 2
    assert all(call[0].endswith("/v2/reference/news") for call in client.calls)
    assert all(call[1]["apiKey"] == "test-key" for call in client.calls)
    assert all(call[1]["sort"] == "published_utc" for call in client.calls)


def test_massive_news_can_filter_one_symbol():
    client = FakeMassiveNewsClient()
    provider = MassiveNewsProvider(api_key="test-key", client=client)

    articles = provider.list_news(symbol="nvda", limit=5)

    assert [article.tickers for article in articles] == [["NVDA"]]
    assert client.calls[0][1]["ticker"] == "NVDA"


def test_massive_news_missing_key_fails_before_request():
    client = FakeMassiveNewsClient()
    provider = MassiveNewsProvider(api_key="", client=client)

    with pytest.raises(NewsProviderConfigurationError, match="MASSIVE_API_KEY"):
        provider.list_news(symbol="NVDA")

    assert client.calls == []


class InvalidMassiveNewsClient:
    def get(self, url: str, *, params: dict, timeout: float) -> httpx.Response:
        return httpx.Response(
            200,
            json={"status": "OK", "results": [{"id": "incomplete"}]},
            request=httpx.Request("GET", url),
        )


def test_massive_invalid_news_is_rejected():
    provider = MassiveNewsProvider(
        api_key="test-key",
        client=InvalidMassiveNewsClient(),
    )

    with pytest.raises(NewsProviderDataError):
        provider.list_news(symbol="NVDA")


class ErrorMassiveNewsClient:
    def get(self, url: str, *, params: dict, timeout: float) -> httpx.Response:
        return httpx.Response(
            403,
            json={"status": "ERROR"},
            request=httpx.Request("GET", url),
        )


def test_massive_news_error_does_not_expose_api_key():
    provider = MassiveNewsProvider(
        api_key="secret-test-key",
        client=ErrorMassiveNewsClient(),
    )

    with pytest.raises(NewsProviderError) as exc_info:
        provider.list_news(symbol="NVDA")

    assert "secret-test-key" not in str(exc_info.value)
