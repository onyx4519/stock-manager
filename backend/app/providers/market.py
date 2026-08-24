from typing import Protocol

from app.schemas.market import StockQuote


class MarketProviderError(RuntimeError):
    """Base exception for market-data provider failures."""


class MarketProviderConfigurationError(MarketProviderError):
    """Raised when a selected market-data provider is not configured."""


class MarketProviderDataError(MarketProviderError):
    """Raised when a provider returns an invalid or incomplete response."""


class MarketProvider(Protocol):
    def list_quotes(self) -> list[StockQuote]: ...

    def get_quote(self, symbol: str) -> StockQuote | None: ...
