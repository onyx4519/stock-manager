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
from app.services.stock_aliases import find_us_tickers_by_korean_alias


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
                    "검색어가 없을 때는 API 호출량을 줄이기 위해 설정된 주요 종목만 표시합니다."
                ],
            )

        items: list[StockSearchItem] = []
        sources: list[str] = []
        warnings: list[str] = []
        contains_hangul = any("가" <= char <= "힣" for char in term)
        contains_latin = any("a" <= char.casefold() <= "z" for char in term)
        per_source_limit = max(1, limit)
        preferred_symbols: list[str] = []

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
                    pass

            used_dart_directory = False
            if contains_latin or not used_kis_directory:
                try:
                    dart_companies = self.dart_provider.search_listed_companies(
                        term,
                        limit=per_source_limit,
                    )
                    domestic.extend(
                        {
                            "symbol": str(company["stock_code"]),
                            "company_name": str(company["corp_name"]),
                            "currency": "KRW",
                            "exchange": "KR",
                        }
                        for company in dart_companies
                        if str(company["stock_code"]).isdigit()
                    )
                    used_dart_directory = True
                    sources.append("OpenDART 영문 기업명")
                except DartProviderError:
                    if contains_latin and used_kis_directory:
                        warnings.append(
                            "OpenDART 영문 기업명 목록을 불러오지 못했습니다."
                        )

            if not used_kis_directory and used_dart_directory:
                warnings.append(
                    "KIS 종목 마스터를 불러오지 못해 OpenDART 목록을 사용했습니다."
                )
            elif not used_kis_directory and not used_dart_directory:
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

        if settings.market_provider in {"hybrid", "massive"}:
            alias_symbols = (
                find_us_tickers_by_korean_alias(term, limit=per_source_limit)
                if contains_hangul
                else ()
            )
            overseas_queries = alias_symbols if contains_hangul else (term,)
            preferred_symbols.extend(alias_symbols)

            if self.massive_provider is None:
                if overseas_queries:
                    warnings.append("미국 종목 디렉터리를 사용할 수 없습니다.")
            else:
                try:
                    overseas: list[dict[str, str]] = []
                    for overseas_query in overseas_queries:
                        matches = self.massive_provider.search_tickers(
                            overseas_query,
                            limit=per_source_limit,
                        )
                        if contains_hangul:
                            matches = [
                                item
                                for item in matches
                                if item["symbol"].casefold()
                                == overseas_query.casefold()
                            ]
                        overseas.extend(matches)
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
                    if overseas_queries:
                        sources.append(
                            "Massive 한글 별칭" if contains_hangul else "Massive"
                        )
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
        items = self._deduplicate_and_rank(
            items,
            term,
            preferred_symbols=preferred_symbols,
        )[:limit]
        if contains_hangul and not items and not preferred_symbols:
            warnings.append(
                "미국 종목의 한글명은 등록된 별칭만 검색할 수 있습니다. "
                "찾지 못하면 영문명이나 티커를 입력해 주세요."
            )
        return StockSearchResponse(
            query=term,
            total_count=len(items),
            items=items,
            sources=list(dict.fromkeys(sources)),
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
        *,
        preferred_symbols: list[str] | None = None,
    ) -> list[StockSearchItem]:
        unique = {item.symbol: item for item in items}
        folded = term.casefold()
        preferred = {
            symbol.casefold(): index
            for index, symbol in enumerate(preferred_symbols or [])
        }

        def rank(item: StockSearchItem) -> tuple[int, int, str]:
            symbol = item.symbol.casefold()
            name = item.company_name.casefold()
            if symbol in preferred:
                return (-1, preferred[symbol], item.symbol)
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
