from dataclasses import dataclass
from decimal import Decimal

from app.calculations.average_cost import calculate_weighted_average_cost
from app.calculations.pnl import realized_pnl
from app.schemas.portfolio import Transaction, TransactionType


class InvalidTransactionLedgerError(ValueError):
    """Raised when transactions would create an impossible position."""


@dataclass
class PositionState:
    symbol: str
    currency: str
    quantity: Decimal = Decimal("0")
    average_cost: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")


def calculate_position_states(
    transactions: list[Transaction],
) -> dict[str, PositionState]:
    states: dict[str, PositionState] = {}
    ordered = sorted(transactions, key=lambda item: (item.executed_at, item.id))

    for transaction in ordered:
        state = states.setdefault(
            transaction.symbol,
            PositionState(
                symbol=transaction.symbol,
                currency=transaction.currency,
            ),
        )
        if state.currency != transaction.currency:
            raise InvalidTransactionLedgerError(
                f"{transaction.symbol} transactions must use one currency."
            )

        costs = transaction.fee + transaction.tax
        if transaction.transaction_type == TransactionType.BUY:
            state.average_cost = calculate_weighted_average_cost(
                state.quantity,
                state.average_cost,
                transaction.quantity,
                transaction.price,
                costs,
            )
            state.quantity += transaction.quantity
            continue

        if transaction.quantity > state.quantity:
            raise InvalidTransactionLedgerError(
                f"{transaction.symbol} sell quantity exceeds the available position."
            )
        state.realized_pnl += realized_pnl(
            transaction.quantity,
            transaction.price,
            state.average_cost,
            transaction.fee,
            transaction.tax,
        )
        state.quantity -= transaction.quantity
        if state.quantity == 0:
            state.average_cost = Decimal("0")

    return states
