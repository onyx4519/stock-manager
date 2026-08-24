from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.dart import DartCompany


class MetricAssessment(StrEnum):
    HEALTHY = "HEALTHY"
    WATCH = "WATCH"
    CAUTION = "CAUTION"
    NOT_EVALUATED = "NOT_EVALUATED"
    UNAVAILABLE = "UNAVAILABLE"


class FinancialRiskLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    UNAVAILABLE = "UNAVAILABLE"


class FinancialMetric(BaseModel):
    code: str = Field(pattern=r"^M\d{6}$")
    name: str
    category: str
    value: float | None = None
    unit: str
    source: str = "OpenDART"
    is_risk_indicator: bool
    assessment: MetricAssessment
    interpretation: str


class FinancialHealthAnalysis(BaseModel):
    company: DartCompany
    business_year: str = Field(pattern=r"^\d{4}$")
    report_code: str = "11011"
    settlement_date: str | None = None
    metrics: list[FinancialMetric]
    financial_risk_score: float | None = Field(default=None, ge=0, le=100)
    financial_risk_level: FinancialRiskLevel
    evaluated_indicators: int = Field(ge=0)
    methodology: str
    warnings: list[str]
