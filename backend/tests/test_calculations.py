from decimal import Decimal
from app.calculations.average_cost import calculate_weighted_average_cost
from app.calculations.pnl import realized_pnl, unrealized_pnl
from app.calculations.fx import convert_currency


def test_weighted_average_cost():
    result = calculate_weighted_average_cost(Decimal("10"), Decimal("100"), Decimal("5"), Decimal("120"))
    assert result == Decimal("106.6666666666666666666666667")


def test_realized_pnl():
    assert realized_pnl(Decimal("3"), Decimal("130"), Decimal("100")) == Decimal("90")


def test_unrealized_pnl():
    assert unrealized_pnl(Decimal("7"), Decimal("120"), Decimal("100")) == Decimal("140")


def test_fx_conversion():
    assert convert_currency(Decimal("100"), Decimal("1350")) == Decimal("135000")
