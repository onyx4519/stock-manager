from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.auth import get_current_user
from app.db import DuplicateWatchlistItemError
from app.dependencies import watchlist_service as service
from app.schemas.watchlist import WatchlistCreate, WatchlistItem
from app.schemas.auth import AuthUser
from app.services.watchlist_service import (
    UnsupportedWatchlistSymbolError,
    WatchlistItemNotFoundError,
)


router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItem])
def list_watchlist(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[WatchlistItem]:
    return service.list_items(user.id)


@router.post("", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
def add_watchlist_item(
    payload: WatchlistCreate,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> WatchlistItem:
    try:
        return service.add_item(user.id, payload.symbol)
    except UnsupportedWatchlistSymbolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DuplicateWatchlistItemError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    symbol: str,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    try:
        service.delete_item(user.id, symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid stock symbol.") from exc
    except WatchlistItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
