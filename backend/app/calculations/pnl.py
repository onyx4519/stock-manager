from decimal import Decimal


def realized_pnl(
    quantity: Decimal,
    sell_price: Decimal,
    average_cost: Decimal,
    sell_fee: Decimal = Decimal("0"),
    tax: Decimal = Decimal("0"),
) -> Decimal:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    proceeds = quantity * sell_price
    cost = quantity * average_cost
    return proceeds - cost - sell_fee - tax


def unrealized_pnl(quantity: Decimal, current_price: Decimal, average_cost: Decimal) -> Decimal:
    if quantity < 0:
        raise ValueError("quantity cannot be negative")
    return quantity * (current_price - average_cost)
