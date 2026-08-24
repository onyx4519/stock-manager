from fastapi import APIRouter, Query

from app.dependencies import market_service as service
from app.schemas.market import StockQuote

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockQuote])
def search_stocks(
    q: str | None = Query(default=None, min_length=1, max_length=100),
) -> list[StockQuote]:
    quotes = service.list_quotes()
    if not q:
        return quotes
    term = q.strip().casefold()
    return [
        quote
        for quote in quotes
        if term in quote.symbol.casefold() or term in quote.company_name.casefold()
    ]
