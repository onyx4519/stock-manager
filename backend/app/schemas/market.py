from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class DataStatus(StrEnum):
    REALTIME = "REALTIME"
    DELAYED = "DELAYED"
    EOD = "EOD"
    MOCK = "MOCK"
    UNAVAILABLE = "UNAVAILABLE"


class StockQuote(BaseModel):
    symbol: str
    company_name: str
    price: float = Field(ge=0)
    change_percent: float
    currency: str
    timestamp: datetime
    data_status: DataStatus
    provider: str


class StockSearchItem(BaseModel):
    symbol: str
    company_name: str
    market: str
    currency: str
    provider: str
    price: float | None = Field(default=None, ge=0)
    change_percent: float | None = None
    timestamp: datetime | None = None
    data_status: DataStatus = DataStatus.UNAVAILABLE


class StockSearchResponse(BaseModel):
    query: str | None = None
    total_count: int = Field(ge=0)
    items: list[StockSearchItem]
    sources: list[str]
    warnings: list[str] = Field(default_factory=list)
