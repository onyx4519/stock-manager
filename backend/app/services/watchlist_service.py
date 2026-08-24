from app.db import WatchlistRepository
from app.schemas.portfolio import TransactionCreate
from app.schemas.watchlist import WatchlistItem
from app.providers.market import MarketProviderError
from app.services.market_service import MarketService


class WatchlistItemNotFoundError(LookupError):
    pass


class UnsupportedWatchlistSymbolError(ValueError):
    pass


class WatchlistService:
    def __init__(
        self,
        repository: WatchlistRepository,
        market_service: MarketService,
    ) -> None:
        self.repository = repository
        self.market_service = market_service

    def list_items(self) -> list[WatchlistItem]:
        items: list[WatchlistItem] = []
        for record in self.repository.list():
            try:
                quote = self.market_service.get_quote(record.symbol)
            except MarketProviderError:
                quote = None
            if quote is None:
                items.append(WatchlistItem(**record.model_dump()))
                continue
            items.append(
                WatchlistItem(
                    **record.model_dump(
                        exclude={"company_name", "currency"}
                    ),
                    company_name=quote.company_name,
                    currency=quote.currency,
                    price=quote.price,
                    change_percent=quote.change_percent,
                    timestamp=quote.timestamp,
                    data_status=quote.data_status,
                    provider=quote.provider,
                )
            )
        return items

    def add_item(self, symbol: str) -> WatchlistItem:
        normalized = TransactionCreate.validate_symbol(symbol)
        quote = self.market_service.get_quote(normalized)
        if quote is None:
            raise UnsupportedWatchlistSymbolError(
                "The selected symbol is not supported by the configured providers."
            )
        record = self.repository.create(quote)
        return WatchlistItem(
            **record.model_dump(),
            price=quote.price,
            change_percent=quote.change_percent,
            timestamp=quote.timestamp,
            data_status=quote.data_status,
            provider=quote.provider,
        )

    def delete_item(self, symbol: str) -> None:
        normalized = TransactionCreate.validate_symbol(symbol)
        if not self.repository.delete(normalized):
            raise WatchlistItemNotFoundError("Watchlist item not found.")
