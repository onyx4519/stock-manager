from collections import defaultdict
from decimal import Decimal

from app.calculations.portfolio import calculate_position_states
from app.db import TransactionRepository
from app.schemas.portfolio import CurrencySummary, PortfolioSummary, Position
from app.services.market_service import MarketService


class PortfolioService:
    def __init__(
        self,
        repository: TransactionRepository,
        market_service: MarketService,
    ) -> None:
        self.repository = repository
        self.market_service = market_service

    def list_positions(self) -> list[Position]:
        states = calculate_position_states(self.repository.list())
        rows: list[dict] = []
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

        for state in states.values():
            if state.quantity == 0:
                continue
            quote = self.market_service.get_quote(state.symbol)
            if quote is None:
                continue
            current_price = Decimal(str(quote.price))
            cost_basis = state.quantity * state.average_cost
            market_value = state.quantity * current_price
            unrealized = market_value - cost_basis
            return_percent = (
                unrealized / cost_basis * Decimal("100")
                if cost_basis > 0
                else Decimal("0")
            )
            totals[state.currency] += market_value
            rows.append(
                {
                    "state": state,
                    "quote": quote,
                    "current_price": current_price,
                    "cost_basis": cost_basis,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized,
                    "return_percent": return_percent,
                }
            )

        positions: list[Position] = []
        for row in rows:
            state = row["state"]
            quote = row["quote"]
            total = totals[state.currency]
            weight = (
                row["market_value"] / total * Decimal("100")
                if total > 0
                else Decimal("0")
            )
            positions.append(
                Position(
                    symbol=state.symbol,
                    company_name=quote.company_name,
                    quantity=state.quantity,
                    average_cost=state.average_cost,
                    current_price=row["current_price"],
                    currency=state.currency,
                    cost_basis=row["cost_basis"],
                    market_value=row["market_value"],
                    realized_pnl=state.realized_pnl,
                    unrealized_pnl=row["unrealized_pnl"],
                    return_percent=row["return_percent"],
                    weight_percent=weight,
                    data_status=quote.data_status,
                    provider=quote.provider,
                    quoted_at=quote.timestamp,
                )
            )
        return sorted(positions, key=lambda item: (item.currency, -item.market_value))

    def get_summary(self) -> PortfolioSummary:
        states = calculate_position_states(self.repository.list())
        positions = self.list_positions()
        summaries: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {
                "cost_basis": Decimal("0"),
                "market_value": Decimal("0"),
                "realized_pnl": Decimal("0"),
                "unrealized_pnl": Decimal("0"),
            }
        )

        for state in states.values():
            summaries[state.currency]["realized_pnl"] += state.realized_pnl
        for position in positions:
            summary = summaries[position.currency]
            summary["cost_basis"] += position.cost_basis
            summary["market_value"] += position.market_value
            summary["unrealized_pnl"] += position.unrealized_pnl

        return PortfolioSummary(
            positions_count=len(positions),
            currencies=[
                CurrencySummary(currency=currency, **values)
                for currency, values in sorted(summaries.items())
            ],
        )
