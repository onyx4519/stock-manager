from app.core.config import settings
from app.providers.dart import DartProvider, DartProviderError
from app.providers.kis import KisMarketProvider
from app.providers.market import MarketProviderError
from app.providers.massive import MassiveMarketProvider
from app.schemas.market import (
    DataStatus,
    StockQuote,
    StockSearchItem,
    StockSearchResponse,
)
from app.services.market_service import MarketService


class StockDirectoryService:
    def __init__(
        self,
        market_service: MarketService,
        *,
        dart_provider: DartProvider | None = None,
        kis_provider: KisMarketProvider | None = None,
        massive_provider: MassiveMarketProvider | None = None,
    ) -> None:
        self.market_service = market_service
        self.dart_provider = dart_provider or DartProvider()
        self.kis_provider = kis_provider or self._resolve_kis_provider()
        self.massive_provider = massive_provider or self._resolve_massive_provider()

    def search(self, query: str | None, *, limit: int = 20) -> StockSearchResponse:
        term = query.strip() if query else ""
        if not term:
            quotes = self.market_service.list_quotes()
            items = [self._from_quote(quote) for quote in quotes[:limit]]
            return StockSearchResponse(
                query=None,
                total_count=len(items),
                items=items,
                sources=sorted({item.provider for item in items}),
                warnings=[
                    "검색어가 없을 때는 API 호출량을 줄이기 위해 설정된 시작 종목만 표시합니다."
                ],
            )

        items: list[StockSearchItem] = []
        sources: list[str] = []
        warnings: list[str] = []
        is_domestic_term = term.isdigit() or any("가" <= char <= "힣" for char in term)
        per_source_limit = max(1, limit if is_domestic_term else (limit + 1) // 2)

        if settings.market_provider in {"hybrid", "kis"}:
            domestic: list[dict[str, str]] = []
            used_kis_directory = False
            if self.kis_provider is not None:
                try:
                    domestic = self.kis_provider.search_tickers(
                        term,
                        limit=per_source_limit,
                    )
                    used_kis_directory = True
                    sources.append("KIS 종목 마스터")
                except MarketProviderError:
                    warnings.append("KIS 종목 마스터를 불러오지 못해 OpenDART 목록을 사용했습니다.")
            if not used_kis_directory:
                try:
                    dart_companies = self.dart_provider.search_listed_companies(
                        term,
                        limit=per_source_limit * 2,
                    )
                    domestic = [
                        {
                            "symbol": str(company["stock_code"]),
                            "company_name": str(company["corp_name"]),
                            "currency": "KRW",
                            "exchange": "KR",
                        }
                        for company in dart_companies
                        if str(company["stock_code"]).isdigit()
                    ][:per_source_limit]
                    sources.append("OpenDART 대체 목록")
                except DartProviderError:
                    warnings.append("국내 종목 디렉터리를 불러오지 못했습니다.")
            items.extend(
                StockSearchItem(
                    symbol=item["symbol"],
                    company_name=item["company_name"],
                    market=item["exchange"],
                    currency="KRW",
                    provider="KIS",
                )
                for item in domestic
            )

        if not is_domestic_term and settings.market_provider in {"hybrid", "massive"}:
            if self.massive_provider is None:
                warnings.append("미국 종목 디렉터리를 사용할 수 없습니다.")
            else:
                try:
                    overseas = self.massive_provider.search_tickers(
                        term,
                        limit=per_source_limit,
                    )
                    items.extend(
                        StockSearchItem(
                            symbol=item["symbol"],
                            company_name=item["company_name"],
                            market="US",
                            currency=item["currency"],
                            provider="Massive",
                        )
                        for item in overseas
                    )
                    sources.append("Massive")
                except MarketProviderError:
                    warnings.append("미국 종목 디렉터리를 불러오지 못했습니다.")

        exact_quote = self._get_exact_quote(term)
        if exact_quote is not None:
            existing = next(
                (item for item in items if item.symbol == exact_quote.symbol),
                None,
            )
            if existing is None:
                items.append(self._from_quote(exact_quote))
            else:
                existing.company_name = exact_quote.company_name
                existing.provider = exact_quote.provider
                existing.price = exact_quote.price
                existing.change_percent = exact_quote.change_percent
                existing.timestamp = exact_quote.timestamp
                existing.data_status = exact_quote.data_status
        items = self._deduplicate_and_rank(items, term)[:limit]
        return StockSearchResponse(
            query=term,
            total_count=len(items),
            items=items,
            sources=sources,
            warnings=warnings,
        )

    def _resolve_massive_provider(self) -> MassiveMarketProvider | None:
        provider = self.market_service.provider
        if isinstance(provider, MassiveMarketProvider):
            return provider
        overseas = getattr(provider, "overseas_provider", None)
        return overseas if isinstance(overseas, MassiveMarketProvider) else None

    def _resolve_kis_provider(self) -> KisMarketProvider | None:
        provider = self.market_service.provider
        if isinstance(provider, KisMarketProvider):
            return provider
        domestic = getattr(provider, "domestic_provider", None)
        return domestic if isinstance(domestic, KisMarketProvider) else None

    def _get_exact_quote(self, term: str) -> StockQuote | None:
        try:
            return self.market_service.get_quote(term.upper())
        except MarketProviderError:
            return None

    @staticmethod
    def _deduplicate_and_rank(
        items: list[StockSearchItem],
        term: str,
    ) -> list[StockSearchItem]:
        unique = {item.symbol: item for item in items}
        folded = term.casefold()

        def rank(item: StockSearchItem) -> tuple[int, int, str]:
            symbol = item.symbol.casefold()
            name = item.company_name.casefold()
            if folded == symbol:
                return (0, len(name), item.symbol)
            if folded == name:
                return (1, len(name), item.symbol)
            if symbol.startswith(folded):
                return (2, len(name), item.symbol)
            if name.startswith(folded):
                return (3, len(name), item.symbol)
            return (4, len(name), item.symbol)

        return sorted(unique.values(), key=rank)

    @staticmethod
    def _from_quote(quote: StockQuote) -> StockSearchItem:
        return StockSearchItem(
            symbol=quote.symbol,
            company_name=quote.company_name,
            market="KR" if quote.currency == "KRW" else "US",
            currency=quote.currency,
            provider=quote.provider,
            price=quote.price,
            change_percent=quote.change_percent,
            timestamp=quote.timestamp,
            data_status=quote.data_status,
        )
