from datetime import datetime
from zoneinfo import ZoneInfo
from app.schemas.market import DataStatus, StockQuote


class MockMarketProvider:
    """Development-only provider. Values are illustrative and must never be treated as live market data."""

    def __init__(self) -> None:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        self._quotes = {
            "NVDA": StockQuote(
                symbol="NVDA",
                company_name="NVIDIA Corporation",
                price=120.50,
                change_percent=1.80,
                currency="USD",
                timestamp=now,
                data_status=DataStatus.MOCK,
                provider="MockProvider",
            ),
            "005930": StockQuote(
                symbol="005930",
                company_name="삼성전자",
                price=78000,
                change_percent=-0.60,
                currency="KRW",
                timestamp=now,
                data_status=DataStatus.MOCK,
                provider="MockProvider",
            ),
        }

    def list_quotes(self) -> list[StockQuote]:
        return list(self._quotes.values())

    def get_quote(self, symbol: str) -> StockQuote | None:
        return self._quotes.get(symbol.upper())
