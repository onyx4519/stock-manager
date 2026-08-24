from fastapi import APIRouter, Query

from app.dependencies import stock_directory_service as service
from app.schemas.market import StockSearchResponse

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=StockSearchResponse)
def search_stocks(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
) -> StockSearchResponse:
    return service.search(q, limit=limit)
