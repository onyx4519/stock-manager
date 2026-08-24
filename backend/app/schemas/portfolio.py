from datetime import datetime
from decimal import Decimal
from enum import StrEnum
import re

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.market import DataStatus


class TransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TransactionCreate(BaseModel):
    symbol: str
    transaction_type: TransactionType
    quantity: Decimal = Field(gt=0, max_digits=30, decimal_places=10)
    price: Decimal = Field(gt=0, max_digits=30, decimal_places=10)
    currency: str
    fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=30, decimal_places=10)
    tax: Decimal = Field(default=Decimal("0"), ge=0, max_digits=30, decimal_places=10)
    executed_at: datetime

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"(?:\d{6}|[A-Z][A-Z0-9.-]{0,14})", normalized):
            raise ValueError("symbol must be a six-digit code or supported ticker")
        return normalized

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", normalized):
            raise ValueError("currency must be a three-letter code")
        return normalized

    @field_validator("executed_at")
    @classmethod
    def validate_executed_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("executed_at must include a timezone")
        return value


class TransactionUpdate(BaseModel):
    symbol: str | None = None
    transaction_type: TransactionType | None = None
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=10)
    price: Decimal | None = Field(default=None, gt=0, max_digits=30, decimal_places=10)
    currency: str | None = None
    fee: Decimal | None = Field(default=None, ge=0, max_digits=30, decimal_places=10)
    tax: Decimal | None = Field(default=None, ge=0, max_digits=30, decimal_places=10)
    executed_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str | None) -> str | None:
        return TransactionCreate.validate_symbol(value) if value is not None else None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str | None) -> str | None:
        return TransactionCreate.validate_currency(value) if value is not None else None

    @field_validator("executed_at")
    @classmethod
    def validate_executed_at(cls, value: datetime | None) -> datetime | None:
        return TransactionCreate.validate_executed_at(value) if value is not None else None

    @model_validator(mode="after")
    def require_change(self):
        if not self.model_fields_set:
            raise ValueError("at least one transaction field is required")
        return self


class Transaction(TransactionCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class Position(BaseModel):
    symbol: str
    company_name: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    currency: str
    cost_basis: Decimal
    market_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    return_percent: Decimal
    weight_percent: Decimal
    data_status: DataStatus
    provider: str
    quoted_at: datetime


class CurrencySummary(BaseModel):
    currency: str
    cost_basis: Decimal
    market_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class PortfolioSummary(BaseModel):
    positions_count: int
    currencies: list[CurrencySummary]
