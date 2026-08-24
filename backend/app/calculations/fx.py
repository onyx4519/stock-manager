from decimal import Decimal


def convert_currency(amount: Decimal, fx_rate: Decimal) -> Decimal:
    if fx_rate <= 0:
        raise ValueError("fx_rate must be positive")
    return amount * fx_rate
