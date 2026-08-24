import type {
  FinancialHealthAnalysis,
  FinancialRiskLevel,
  MetricAssessment,
} from "@/types/market";


const riskLabels: Record<FinancialRiskLevel, string> = {
  LOW: "낮음",
  MODERATE: "보통",
  HIGH: "높음",
  UNAVAILABLE: "산출 불가",
};

const assessmentLabels: Record<MetricAssessment, string> = {
  HEALTHY: "일반 양호",
  WATCH: "관찰",
  CAUTION: "주의",
  NOT_EVALUATED: "점수 미반영",
  UNAVAILABLE: "값 없음",
};


function metricValue(value: number | null, unit: string) {
  if (value === null) return "-";
  return `${value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}${unit}`;
}


export function FinancialAnalysisSection({
  data,
  error,
}: {
  data: FinancialHealthAnalysis | null;
  error: string | null;
}) {
  return (
    <section>
      <div className="rowBetween gap sectionTitleRow">
        <div>
          <h2>재무비율·재무 위험 신호</h2>
          <p className="meta analysisSubtitle">OpenDART 공식 지표와 일반 기준을 분리해 표시합니다.</p>
        </div>
        {data && (
          <span className="sourceBadge">
            OpenDART · {data.businessYear} 사업보고서
          </span>
        )}
      </div>
      {error ? (
        <div className="card emptyState">{error}</div>
      ) : !data ? (
        <div className="card emptyState">재무 분석 데이터가 없습니다.</div>
      ) : (
        <div className="analysisStack">
          <div className="analysisSummaryGrid">
            <div className="card analysisScoreCard">
              <span className="muted">일반 재무 위험 신호</span>
              <div className="analysisScoreRow">
                <strong>
                  {data.financialRiskScore === null ? "-" : `${data.financialRiskScore.toFixed(1)}점`}
                </strong>
                <span className={`riskLevel riskLevel-${data.financialRiskLevel.toLowerCase()}`}>
                  {riskLabels[data.financialRiskLevel]}
                </span>
              </div>
              <p className="meta">핵심 지표 {data.evaluatedIndicators}/4개 평가 · 점수가 높을수록 주의 신호가 많습니다.</p>
            </div>
            <div className="card analysisMethodCard">
              <span className="muted">산출 방법</span>
              <p>{data.methodology}</p>
              {data.settlementDate && <div className="meta">결산기준일 {data.settlementDate}</div>}
            </div>
          </div>
          <div className="analysisMetricGrid">
            {data.metrics.map((metric) => (
              <div className="card analysisMetric" key={metric.code}>
                <div className="rowBetween gap">
                  <div>
                    <span className="eyebrow">{metric.category}</span>
                    <h3>{metric.name}</h3>
                  </div>
                  <span className={`metricAssessment metricAssessment-${metric.assessment.toLowerCase()}`}>
                    {assessmentLabels[metric.assessment]}
                  </span>
                </div>
                <strong className="analysisMetricValue">{metricValue(metric.value, metric.unit)}</strong>
                <p className="meta">{metric.interpretation}</p>
                <div className="metricSource">{metric.source} · {metric.code}</div>
              </div>
            ))}
          </div>
          <div className="card analysisWarnings">
            <strong>해석 주의사항</strong>
            <ul>
              {data.warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          </div>
        </div>
      )}
    </section>
  );
}
