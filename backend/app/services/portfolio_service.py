from app.schemas.portfolio import Position


class PortfolioService:
    """Mock portfolio until persistent transaction storage is connected."""

    def list_positions(self) -> list[Position]:
        return [
            Position(symbol="NVDA", company_name="NVIDIA Corporation", quantity=5, average_cost=108, current_price=120.5, currency="USD", market_value=602.5, unrealized_pnl=62.5, weight_percent=42.4),
            Position(symbol="005930", company_name="삼성전자", quantity=10, average_cost=75000, current_price=78000, currency="KRW", market_value=780000, unrealized_pnl=30000, weight_percent=57.6),
        ]
