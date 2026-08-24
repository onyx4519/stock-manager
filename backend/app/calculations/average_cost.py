from decimal import Decimal


def calculate_weighted_average_cost(
    existing_quantity: Decimal,
    existing_average_cost: Decimal,
    buy_quantity: Decimal,
    buy_price: Decimal,
    buy_fee: Decimal = Decimal("0"),
) -> Decimal:
    """Return cost per share after a new purchase. Internal math keeps Decimal precision."""
    if existing_quantity < 0 or buy_quantity <= 0:
        raise ValueError("quantities must be valid")

    existing_cost = existing_quantity * existing_average_cost
    new_cost = buy_quantity * buy_price + buy_fee
    total_quantity = existing_quantity + buy_quantity
    return (existing_cost + new_cost) / total_quantity
