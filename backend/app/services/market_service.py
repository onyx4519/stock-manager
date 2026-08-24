from app.providers.mock.market_provider import MockMarketProvider
from app.schemas.market import StockQuote


class MarketService:
    def __init__(self) -> None:
        self.provider = MockMarketProvider()

    def list_quotes(self) -> list[StockQuote]:
        return self.provider.list_quotes()

    def get_quote(self, symbol: str) -> StockQuote | None:
        return self.provider.get_quote(symbol)
