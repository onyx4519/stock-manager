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
