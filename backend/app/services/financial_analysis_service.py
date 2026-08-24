from dataclasses import dataclass

from app.schemas.analysis import (
    FinancialHealthAnalysis,
    FinancialMetric,
    FinancialRiskLevel,
    MetricAssessment,
)
from app.schemas.dart import DartCompany


@dataclass(frozen=True)
class MetricDefinition:
    code: str
    name: str
    category: str
    risk_indicator: bool = False


METRIC_DEFINITIONS = (
    MetricDefinition("M211200", "매출액순이익률", "수익성", True),
    MetricDefinition("M211550", "자기자본이익률(ROE)", "수익성"),
    MetricDefinition("M221000", "자기자본비율", "안정성"),
    MetricDefinition("M221100", "부채비율", "안정성", True),
    MetricDefinition("M221200", "유동비율", "안정성", True),
    MetricDefinition("M231000", "매출액증가율", "성장성", True),
    MetricDefinition("M231400", "영업이익증가율", "성장성"),
    MetricDefinition("M231800", "당기순이익증가율", "성장성"),
    MetricDefinition("M233000", "총자산증가율", "성장성"),
)


class FinancialAnalysisService:
    METHODOLOGY = (
        "OpenDART 공식 재무지표 중 순이익률·부채비율·유동비율·"
        "매출액증가율을 각각 0~2점으로 평가한 뒤 100점으로 환산합니다. "
        "점수가 높을수록 일반 재무 위험 신호가 많다는 의미입니다."
    )

    def analyze(
        self,
        *,
        company: DartCompany,
        business_year: int,
        indicators: list[dict],
    ) -> FinancialHealthAnalysis:
        values = {
            item.get("indicator_code"): item.get("value")
            for item in indicators
            if isinstance(item.get("indicator_code"), str)
        }
        metrics: list[FinancialMetric] = []
        risk_points = 0
        evaluated_indicators = 0

        for definition in METRIC_DEFINITIONS:
            raw_value = values.get(definition.code)
            value = float(raw_value) if isinstance(raw_value, (int, float)) else None
            assessment, points, interpretation = self._assess(definition.code, value)
            if definition.risk_indicator and value is not None:
                evaluated_indicators += 1
                risk_points += points
            metrics.append(
                FinancialMetric(
                    code=definition.code,
                    name=definition.name,
                    category=definition.category,
                    value=round(value, 3) if value is not None else None,
                    unit="%",
                    is_risk_indicator=definition.risk_indicator,
                    assessment=assessment,
                    interpretation=interpretation,
                )
            )

        warnings = [
            "업종·기업규모·회계정책을 보정하지 않은 일반 재무 신호이며 투자등급이 아닙니다.",
            "OpenDART 자료는 제출인의 책임으로 작성되며 정정 공시에 따라 변경될 수 있습니다.",
        ]
        if evaluated_indicators < 3:
            risk_score = None
            risk_level = FinancialRiskLevel.UNAVAILABLE
            warnings.append(
                "핵심 지표가 3개 미만이므로 종합 위험 신호를 산출하지 않았습니다."
            )
        else:
            risk_score = round(
                risk_points / (evaluated_indicators * 2) * 100,
                1,
            )
            if risk_score < 25:
                risk_level = FinancialRiskLevel.LOW
            elif risk_score < 50:
                risk_level = FinancialRiskLevel.MODERATE
            else:
                risk_level = FinancialRiskLevel.HIGH

        settlement_date = next(
            (
                item.get("settlement_date")
                for item in indicators
                if isinstance(item.get("settlement_date"), str)
            ),
            None,
        )
        return FinancialHealthAnalysis(
            company=company,
            business_year=str(business_year),
            settlement_date=settlement_date,
            metrics=metrics,
            financial_risk_score=risk_score,
            financial_risk_level=risk_level,
            evaluated_indicators=evaluated_indicators,
            methodology=self.METHODOLOGY,
            warnings=warnings,
        )

    @staticmethod
    def _assess(
        code: str,
        value: float | None,
    ) -> tuple[MetricAssessment, int, str]:
        if value is None:
            return MetricAssessment.UNAVAILABLE, 0, "OpenDART 제공값이 없습니다."

        if code == "M211200":
            if value < 0:
                return MetricAssessment.CAUTION, 2, "순손실 구간으로 주의 신호입니다."
            if value < 5:
                return MetricAssessment.WATCH, 1, "5% 미만으로 관찰 신호입니다."
            return MetricAssessment.HEALTHY, 0, "5% 이상으로 일반 기준상 양호합니다."
        if code == "M221100":
            if value >= 200:
                return MetricAssessment.CAUTION, 2, "200% 이상으로 주의 신호입니다."
            if value >= 100:
                return MetricAssessment.WATCH, 1, "100% 이상으로 관찰 신호입니다."
            return MetricAssessment.HEALTHY, 0, "100% 미만으로 일반 기준상 양호합니다."
        if code == "M221200":
            if value < 100:
                return MetricAssessment.CAUTION, 2, "100% 미만으로 주의 신호입니다."
            if value < 150:
                return MetricAssessment.WATCH, 1, "150% 미만으로 관찰 신호입니다."
            return MetricAssessment.HEALTHY, 0, "150% 이상으로 일반 기준상 양호합니다."
        if code == "M231000":
            if value < -10:
                return MetricAssessment.CAUTION, 2, "전년 대비 10% 초과 감소한 주의 신호입니다."
            if value < 0:
                return MetricAssessment.WATCH, 1, "전년 대비 감소한 관찰 신호입니다."
            return MetricAssessment.HEALTHY, 0, "전년 대비 증가한 일반 양호 신호입니다."

        return (
            MetricAssessment.NOT_EVALUATED,
            0,
            "OpenDART 공식 지표이며 종합 위험 점수에는 사용하지 않습니다.",
        )
