from datetime import datetime

from pydantic import BaseModel, field_validator

from app.schemas.market import DataStatus
from app.schemas.portfolio import TransactionCreate


class WatchlistCreate(BaseModel):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        return TransactionCreate.validate_symbol(value)


class WatchlistRecord(BaseModel):
    symbol: str
    company_name: str
    currency: str
    created_at: datetime


class WatchlistItem(WatchlistRecord):
    price: float | None = None
    change_percent: float | None = None
    timestamp: datetime | None = None
    data_status: DataStatus = DataStatus.UNAVAILABLE
    provider: str | None = None
