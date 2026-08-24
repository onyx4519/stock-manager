from datetime import datetime, timezone

from app.calculations.portfolio import (
    InvalidTransactionLedgerError,
    calculate_position_states,
)
from app.db import TransactionRepository
from app.schemas.portfolio import Transaction, TransactionCreate, TransactionUpdate
from app.services.market_service import MarketService


class TransactionNotFoundError(LookupError):
    pass


class UnsupportedTransactionSymbolError(ValueError):
    pass


class TransactionService:
    def __init__(
        self,
        repository: TransactionRepository,
        market_service: MarketService,
    ) -> None:
        self.repository = repository
        self.market_service = market_service

    def list_transactions(self, user_id: str, *, symbol: str | None = None) -> list[Transaction]:
        normalized_symbol = (
            TransactionCreate.validate_symbol(symbol) if symbol is not None else None
        )
        return self.repository.list(user_id, symbol=normalized_symbol)

    def get_transaction(self, user_id: str, transaction_id: int) -> Transaction:
        transaction = self.repository.get(user_id, transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("Transaction not found.")
        return transaction

    def create_transaction(self, user_id: str, transaction: TransactionCreate) -> Transaction:
        self._validate_quote(transaction)
        existing = self.repository.list(user_id)
        next_id = max((item.id for item in existing), default=0) + 1
        candidate = self._candidate(transaction, transaction_id=next_id)
        calculate_position_states([*existing, candidate])
        return self.repository.create(user_id, transaction)

    def update_transaction(
        self,
        user_id: str,
        transaction_id: int,
        changes: TransactionUpdate,
    ) -> Transaction:
        existing = self.get_transaction(user_id, transaction_id)
        merged = TransactionCreate.model_validate(
            {
                **existing.model_dump(
                    include={
                        "symbol",
                        "transaction_type",
                        "quantity",
                        "price",
                        "currency",
                        "fee",
                        "tax",
                        "executed_at",
                    }
                ),
                **changes.model_dump(exclude_none=True),
            }
        )
        self._validate_quote(merged)
        candidate = self._candidate(merged, transaction_id=transaction_id)
        remaining = [
            item for item in self.repository.list(user_id) if item.id != transaction_id
        ]
        calculate_position_states([*remaining, candidate])
        updated = self.repository.update(user_id, transaction_id, merged)
        if updated is None:
            raise TransactionNotFoundError("Transaction not found.")
        return updated

    def delete_transaction(self, user_id: str, transaction_id: int) -> None:
        self.get_transaction(user_id, transaction_id)
        remaining = [
            item for item in self.repository.list(user_id) if item.id != transaction_id
        ]
        calculate_position_states(remaining)
        if not self.repository.delete(user_id, transaction_id):
            raise TransactionNotFoundError("Transaction not found.")

    def _validate_quote(self, transaction: TransactionCreate) -> None:
        quote = self.market_service.get_quote(transaction.symbol)
        if quote is None:
            raise UnsupportedTransactionSymbolError(
                "The selected symbol is not supported by the configured providers."
            )
        if quote.currency != transaction.currency:
            raise UnsupportedTransactionSymbolError(
                f"{transaction.symbol} transactions must use {quote.currency}."
            )

    @staticmethod
    def _candidate(
        transaction: TransactionCreate,
        *,
        transaction_id: int = 0,
    ) -> Transaction:
        now = datetime.now(timezone.utc)
        return Transaction(
            id=transaction_id,
            **transaction.model_dump(),
            created_at=now,
            updated_at=now,
        )


__all__ = [
    "InvalidTransactionLedgerError",
    "TransactionNotFoundError",
    "TransactionService",
    "UnsupportedTransactionSymbolError",
]
