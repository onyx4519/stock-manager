import re
import time
from datetime import datetime
from threading import RLock

import httpx

from app.core.config import settings
from app.providers.news import (
    NewsProviderConfigurationError,
    NewsProviderDataError,
    NewsProviderError,
)
from app.schemas.news import NewsArticle


class MassiveNewsProvider:
    BASE_URL = "https://api.massive.com"
    SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,14}$")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        symbols: tuple[str, ...] | None = None,
        cache_seconds: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = settings.massive_api_key if api_key is None else api_key
        self.symbols = settings.massive_symbols if symbols is None else symbols
        self.cache_seconds = (
            settings.massive_news_cache_seconds
            if cache_seconds is None
            else cache_seconds
        )
        self._client = client
        self._cache: dict[str, tuple[float, int, list[NewsArticle]]] = {}
        self._cache_lock = RLock()

    def list_news(
        self,
        *,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[NewsArticle]:
        if not self.api_key:
            raise NewsProviderConfigurationError(
                "MASSIVE_API_KEY is not configured."
            )

        requested_symbols = (symbol,) if symbol is not None else self.symbols
        normalized_symbols = tuple(
            dict.fromkeys(item.strip().upper() for item in requested_symbols)
        )
        if any(
            not self.SYMBOL_PATTERN.fullmatch(item) for item in normalized_symbols
        ):
            raise NewsProviderDataError("A news ticker symbol is invalid.")

        articles = [
            article
            for item in normalized_symbols
            for article in self._get_symbol_news(item, limit=limit)
        ]
        unique_articles = {article.id: article for article in articles}
        return sorted(
            unique_articles.values(),
            key=lambda article: article.published_at,
            reverse=True,
        )[:limit]

    def _get_symbol_news(self, symbol: str, *, limit: int) -> list[NewsArticle]:
        with self._cache_lock:
            now = time.monotonic()
            cached = self._cache.get(symbol)
            if (
                cached is not None
                and now - cached[0] < self.cache_seconds
                and cached[1] >= limit
            ):
                return [article.model_copy() for article in cached[2][:limit]]

            payload = self._request_json(
                "/v2/reference/news",
                params={
                    "ticker": symbol,
                    "order": "desc",
                    "sort": "published_utc",
                    "limit": limit,
                },
            )
            results = payload.get("results", [])
            if not isinstance(results, list) or not all(
                isinstance(item, dict) for item in results
            ):
                raise NewsProviderDataError("Massive news results are invalid.")

            articles = [self._normalize_article(item) for item in results]
            self._cache[symbol] = (now, limit, articles)
            return [article.model_copy() for article in articles]

    def _request_json(self, path: str, *, params: dict) -> dict:
        request_params = dict(params)
        request_params["apiKey"] = self.api_key
        request = self._client.get if self._client is not None else httpx.get
        try:
            response = request(
                f"{self.BASE_URL}{path}",
                params=request_params,
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise NewsProviderError("Massive news request failed.") from exc

        if not isinstance(payload, dict):
            raise NewsProviderDataError("Massive returned a non-object response.")
        if payload.get("status") not in {"OK", "DELAYED"}:
            raise NewsProviderError("Massive returned an error status for news.")
        return payload

    @staticmethod
    def _normalize_article(item: dict) -> NewsArticle:
        publisher = item.get("publisher")
        tickers = item.get("tickers")
        if not isinstance(publisher, dict):
            raise NewsProviderDataError("Massive news publisher is missing.")
        if not isinstance(tickers, list) or not all(
            isinstance(ticker, str) for ticker in tickers
        ):
            raise NewsProviderDataError("Massive news tickers are invalid.")

        required_strings = {
            "id": item.get("id"),
            "title": item.get("title"),
            "article_url": item.get("article_url"),
            "published_at": item.get("published_utc"),
            "publisher_name": publisher.get("name"),
        }
        if any(
            not isinstance(value, str) or not value.strip()
            for value in required_strings.values()
        ):
            raise NewsProviderDataError("Massive news article is incomplete.")

        try:
            published_at = datetime.fromisoformat(
                required_strings["published_at"].replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise NewsProviderDataError(
                "Massive news publication time is invalid."
            ) from exc

        def optional_string(value: object) -> str | None:
            return value.strip() if isinstance(value, str) and value.strip() else None

        return NewsArticle(
            id=required_strings["id"].strip(),
            title=required_strings["title"].strip(),
            author=optional_string(item.get("author")),
            description=optional_string(item.get("description")),
            article_url=required_strings["article_url"].strip(),
            image_url=optional_string(item.get("image_url")),
            publisher_name=required_strings["publisher_name"].strip(),
            publisher_homepage_url=optional_string(publisher.get("homepage_url")),
            published_at=published_at,
            tickers=list(dict.fromkeys(ticker.strip().upper() for ticker in tickers)),
        )
