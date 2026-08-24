from typing import Protocol

from app.schemas.news import NewsArticle


class NewsProviderError(RuntimeError):
    """Base exception for news-provider failures."""


class NewsProviderConfigurationError(NewsProviderError):
    """Raised when the news provider is not configured."""


class NewsProviderDataError(NewsProviderError):
    """Raised when the provider returns invalid news data."""


class NewsProvider(Protocol):
    symbols: tuple[str, ...]

    def list_news(
        self,
        *,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[NewsArticle]: ...
