import pytest

from app.schemas.analysis import FinancialRiskLevel, MetricAssessment
from app.schemas.dart import DartCompany
from app.services.financial_analysis_service import FinancialAnalysisService


COMPANY = DartCompany(
    corp_code="00126380",
    corp_name="삼성전자",
    corp_eng_name="SAMSUNG ELECTRONICS CO.,LTD",
    stock_code="005930",
    modify_date="20260101",
)


def indicator(code: str, value: float | None) -> dict:
    return {
        "indicator_code": code,
        "value": value,
        "settlement_date": "2025-12-31",
    }


def test_financial_analysis_uses_only_four_declared_risk_indicators():
    service = FinancialAnalysisService()
    analysis = service.analyze(
        company=COMPANY,
        business_year=2025,
        indicators=[
            indicator("M211200", 13.551),
            indicator("M211550", 10.783),
            indicator("M221000", 76.96),
            indicator("M221100", 29.937),
            indicator("M221200", 232.761),
            indicator("M231000", 10.88),
            indicator("M231400", 33.231),
            indicator("M231800", 31.219),
            indicator("M233000", 10.186),
        ],
    )

    assert len(analysis.metrics) == 9
    assert analysis.evaluated_indicators == 4
    assert analysis.financial_risk_score == 0.0
    assert analysis.financial_risk_level == FinancialRiskLevel.LOW
    assert analysis.settlement_date == "2025-12-31"
    assert analysis.metrics[0].assessment == MetricAssessment.HEALTHY
    assert analysis.metrics[1].assessment == MetricAssessment.NOT_EVALUATED


def test_financial_analysis_flags_high_risk_signals():
    analysis = FinancialAnalysisService().analyze(
        company=COMPANY,
        business_year=2025,
        indicators=[
            indicator("M211200", -3.0),
            indicator("M221100", 250.0),
            indicator("M221200", 80.0),
            indicator("M231000", -12.0),
        ],
    )

    assert analysis.financial_risk_score == 100.0
    assert analysis.financial_risk_level == FinancialRiskLevel.HIGH
    assert all(
        metric.assessment == MetricAssessment.CAUTION
        for metric in analysis.metrics
        if metric.is_risk_indicator
    )


def test_financial_analysis_with_insufficient_data_has_no_score():
    analysis = FinancialAnalysisService().analyze(
        company=COMPANY,
        business_year=2025,
        indicators=[indicator("M221100", 80.0)],
    )

    assert analysis.financial_risk_score is None
    assert analysis.financial_risk_level == FinancialRiskLevel.UNAVAILABLE
    assert analysis.evaluated_indicators == 1
    assert "3개 미만" in analysis.warnings[-1]


@pytest.mark.parametrize(
    ("code", "value", "expected"),
    [
        ("M211200", 0.0, MetricAssessment.WATCH),
        ("M211200", 5.0, MetricAssessment.HEALTHY),
        ("M221100", 100.0, MetricAssessment.WATCH),
        ("M221100", 200.0, MetricAssessment.CAUTION),
        ("M221200", 100.0, MetricAssessment.WATCH),
        ("M221200", 150.0, MetricAssessment.HEALTHY),
        ("M231000", -10.0, MetricAssessment.WATCH),
        ("M231000", 0.0, MetricAssessment.HEALTHY),
    ],
)
def test_financial_risk_threshold_boundaries(code, value, expected):
    assessment, _points, _interpretation = FinancialAnalysisService._assess(
        code,
        value,
    )

    assert assessment == expected
