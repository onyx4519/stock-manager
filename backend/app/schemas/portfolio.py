from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class TransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TransactionCreate(BaseModel):
    symbol: str
    transaction_type: TransactionType
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    currency: str
    fee: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    fx_rate: float | None = Field(default=None, gt=0)
    executed_at: datetime


class Position(BaseModel):
    symbol: str
    company_name: str
    quantity: float
    average_cost: float
    current_price: float
    currency: str
    market_value: float
    unrealized_pnl: float
    weight_percent: float
