import re

from app.providers.market import MarketProvider
from app.schemas.market import StockQuote


class HybridMarketProvider:
    DOMESTIC_SYMBOL_PATTERN = re.compile(r"^\d{6}$")

    def __init__(
        self,
        *,
        domestic_provider: MarketProvider,
        overseas_provider: MarketProvider,
    ) -> None:
        self.domestic_provider = domestic_provider
        self.overseas_provider = overseas_provider

    def list_quotes(self) -> list[StockQuote]:
        return [
            *self.domestic_provider.list_quotes(),
            *self.overseas_provider.list_quotes(),
        ]

    def get_quote(self, symbol: str) -> StockQuote | None:
        normalized_symbol = symbol.strip().upper()
        if self.DOMESTIC_SYMBOL_PATTERN.fullmatch(normalized_symbol):
            return self.domestic_provider.get_quote(normalized_symbol)
        return self.overseas_provider.get_quote(normalized_symbol)
