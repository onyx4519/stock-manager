from fastapi import APIRouter
from app.dependencies import market_service as service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("")
def search_stocks(q: str | None = None):
    quotes = service.list_quotes()
    if not q:
        return quotes
    term = q.lower()
    return [x for x in quotes if term in x.symbol.lower() or term in x.company_name.lower()]
