from app.core.config import settings
from app.services.stock_aliases import find_us_tickers_by_korean_alias
from app.services.stock_directory_service import StockDirectoryService


class StubMarketService:
    provider = object()

    def list_quotes(self):
        return []

    def get_quote(self, _symbol):
        return None


class StubKisProvider:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_tickers(self, query: str, *, limit: int):
        self.queries.append(query)
        return []


class StubDartProvider:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_listed_companies(self, query: str, *, limit: int):
        self.queries.append(query)
        if query.casefold() == "samsung electronics":
            return [
                {
                    "corp_code": "00126380",
                    "corp_name": "삼성전자",
                    "corp_eng_name": "SAMSUNG ELECTRONICS CO.,LTD",
                    "stock_code": "005930",
                    "modify_date": "20260101",
                }
            ]
        return []


class StubMassiveProvider:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_tickers(self, query: str, *, limit: int):
        self.queries.append(query)
        if query == "JOBY":
            return [
                {
                    "symbol": "JOBY",
                    "company_name": "Joby Aviation, Inc.",
                    "currency": "USD",
                },
                {
                    "symbol": "JOBX",
                    "company_name": "Unrelated Job Fund",
                    "currency": "USD",
                },
            ]
        return []


def make_service():
    kis = StubKisProvider()
    dart = StubDartProvider()
    massive = StubMassiveProvider()
    service = StockDirectoryService(
        StubMarketService(),
        kis_provider=kis,
        dart_provider=dart,
        massive_provider=massive,
    )
    return service, kis, dart, massive


def test_korean_us_aliases_ignore_spacing_and_support_partial_names():
    assert find_us_tickers_by_korean_alias("조비 에비에이션") == ("JOBY",)
    assert find_us_tickers_by_korean_alias("조비") == ("JOBY",)


def test_searches_us_stock_by_korean_alias(monkeypatch):
    monkeypatch.setattr(settings, "market_provider", "hybrid")
    service, kis, dart, massive = make_service()

    result = service.search("조비 에비에이션")

    assert [item.symbol for item in result.items] == ["JOBY"]
    assert result.items[0].company_name == "Joby Aviation, Inc."
    assert result.sources == ["KIS 종목 마스터", "Massive 한글 별칭"]
    assert kis.queries == ["조비 에비에이션"]
    assert dart.queries == []
    assert massive.queries == ["JOBY"]


def test_searches_korean_company_by_official_english_name(monkeypatch):
    monkeypatch.setattr(settings, "market_provider", "hybrid")
    service, kis, dart, massive = make_service()

    result = service.search("Samsung Electronics")

    assert [item.symbol for item in result.items] == ["005930"]
    assert result.items[0].company_name == "삼성전자"
    assert "OpenDART 영문 기업명" in result.sources
    assert kis.queries == ["Samsung Electronics"]
    assert dart.queries == ["Samsung Electronics"]
    assert massive.queries == ["Samsung Electronics"]
