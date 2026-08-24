from fastapi import APIRouter, HTTPException
from app.dependencies import market_service as service
from app.schemas.market import StockQuote

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/quotes", response_model=list[StockQuote])
def list_quotes() -> list[StockQuote]:
    return service.list_quotes()


@router.get("/quotes/{symbol}", response_model=StockQuote)
def get_quote(symbol: str) -> StockQuote:
    quote = service.get_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote
