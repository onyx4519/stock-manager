from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.providers.massive import MassiveNewsProvider
from app.providers.news import (
    NewsProviderConfigurationError,
    NewsProviderError,
)
from app.schemas.news import NewsFeed


router = APIRouter(prefix="/news", tags=["news"])
_provider = MassiveNewsProvider()


def get_news_provider() -> MassiveNewsProvider:
    return _provider


@router.get("", response_model=NewsFeed)
def list_news(
    provider: Annotated[MassiveNewsProvider, Depends(get_news_provider)],
    symbol: Annotated[
        str | None,
        Query(pattern=r"^[A-Za-z][A-Za-z0-9.-]{0,14}$"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NewsFeed:
    try:
        items = provider.list_news(symbol=symbol, limit=limit)
    except NewsProviderConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MASSIVE_API_KEY is not configured.",
        ) from exc
    except NewsProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Massive news is unavailable or returned invalid data.",
        ) from exc

    symbols = [symbol.upper()] if symbol else list(provider.symbols)
    return NewsFeed(symbols=symbols, items=items, total_count=len(items))
