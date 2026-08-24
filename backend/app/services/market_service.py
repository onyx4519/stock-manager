from app.core.config import settings
from app.providers.market import MarketProvider
from app.providers.massive import MassiveMarketProvider
from app.providers.mock.market_provider import MockMarketProvider
from app.schemas.market import StockQuote


class MarketService:
    def __init__(self, provider: MarketProvider | None = None) -> None:
        self.provider = provider if provider is not None else self._build_provider()

    def list_quotes(self) -> list[StockQuote]:
        return self.provider.list_quotes()

    def get_quote(self, symbol: str) -> StockQuote | None:
        return self.provider.get_quote(symbol)

    @staticmethod
    def _build_provider() -> MarketProvider:
        if settings.market_provider == "massive":
            return MassiveMarketProvider()
        return MockMarketProvider()
