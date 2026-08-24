from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.auth import get_current_user
from app.calculations.portfolio import InvalidTransactionLedgerError
from app.dependencies import transaction_service as service
from app.schemas.portfolio import Transaction, TransactionCreate, TransactionUpdate
from app.schemas.auth import AuthUser
from app.services.transaction_service import (
    TransactionNotFoundError,
    UnsupportedTransactionSymbolError,
)


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[Transaction])
def list_transactions(
    user: Annotated[AuthUser, Depends(get_current_user)],
    symbol: str | None = Query(default=None, min_length=1, max_length=15),
) -> list[Transaction]:
    return service.list_transactions(user.id, symbol=symbol)


@router.get("/{transaction_id}", response_model=Transaction)
def get_transaction(
    transaction_id: int,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> Transaction:
    try:
        return service.get_transaction(user.id, transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found.") from exc


@router.post("", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: TransactionCreate,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> Transaction:
    try:
        return service.create_transaction(user.id, transaction)
    except UnsupportedTransactionSymbolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidTransactionLedgerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{transaction_id}", response_model=Transaction)
def update_transaction(
    transaction_id: int,
    changes: TransactionUpdate,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> Transaction:
    try:
        return service.update_transaction(user.id, transaction_id, changes)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found.") from exc
    except UnsupportedTransactionSymbolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidTransactionLedgerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> Response:
    try:
        service.delete_transaction(user.id, transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Transaction not found.") from exc
    except InvalidTransactionLedgerError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
