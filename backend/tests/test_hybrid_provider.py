from app.providers.hybrid import HybridMarketProvider
from app.schemas.market import DataStatus, StockQuote


def quote(symbol: str, provider: str) -> StockQuote:
    return StockQuote(
        symbol=symbol,
        company_name=symbol,
        price=100,
        change_percent=1,
        currency="KRW" if symbol.isdigit() else "USD",
        timestamp="2026-08-21T15:30:00+09:00",
        data_status=DataStatus.EOD,
        provider=provider,
    )


class StubProvider:
    def __init__(self, quotes: list[StockQuote]) -> None:
        self.quotes = quotes
        self.requested_symbols: list[str] = []

    def list_quotes(self) -> list[StockQuote]:
        return [item.model_copy() for item in self.quotes]

    def get_quote(self, symbol: str) -> StockQuote | None:
        self.requested_symbols.append(symbol)
        return next((item.model_copy() for item in self.quotes if item.symbol == symbol), None)


def test_hybrid_provider_combines_domestic_and_overseas_quotes():
    domestic = StubProvider([quote("005930", "KIS")])
    overseas = StubProvider([quote("NVDA", "Massive")])
    provider = HybridMarketProvider(
        domestic_provider=domestic,
        overseas_provider=overseas,
    )

    assert [item.symbol for item in provider.list_quotes()] == ["005930", "NVDA"]


def test_hybrid_provider_routes_symbols_by_format():
    domestic = StubProvider([quote("005930", "KIS")])
    overseas = StubProvider([quote("NVDA", "Massive")])
    provider = HybridMarketProvider(
        domestic_provider=domestic,
        overseas_provider=overseas,
    )

    assert provider.get_quote("005930").provider == "KIS"
    assert provider.get_quote("nvda").provider == "Massive"
    assert domestic.requested_symbols == ["005930"]
    assert overseas.requested_symbols == ["NVDA"]
