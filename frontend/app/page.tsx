import { QuoteCard } from "@/components/QuoteCard";
import { ApiMessage } from "@/components/ApiMessage";
import Link from "next/link";
import { getCurrentUser, getPortfolioSummary, getQuotes } from "@/lib/api";

export default async function DashboardPage() {
  const currentUser = await getCurrentUser().catch(() => null);
  const [quoteResult, portfolioResult] = await Promise.all([
    getQuotes()
    .then((quotes) => ({ quotes, error: null }))
    .catch((error: Error) => ({ quotes: [], error: error.message })),
    currentUser ? getPortfolioSummary()
      .then((summary) => ({ summary, error: null }))
      .catch((error: Error) => ({ summary: null, error: error.message }))
      : Promise.resolve({ summary: null, error: null }),
  ]);
  return (
    <div className="page">
      <div className="pageHeader">
        <div><div className="eyebrow">Dashboard</div><h1>오늘의 투자 현황</h1></div>
        <p className="muted">실제 EOD 시세와 저장된 거래 원장을 기준으로 계산합니다.</p>
      </div>

      <section>
        <h2>시장·관심 시세</h2>
        {quoteResult.error ? (
          <ApiMessage title="시세를 불러오지 못했습니다" message={quoteResult.error} />
        ) : quoteResult.quotes.length === 0 ? (
          <ApiMessage title="표시할 시세가 없습니다" message="MASSIVE_SYMBOLS 설정을 확인해 주세요." />
        ) : (
          <div className="grid2">{quoteResult.quotes.map(q => <QuoteCard key={q.symbol} quote={q} />)}</div>
        )}
      </section>

      <section>
        <h2>내 포트폴리오</h2>
        {!currentUser ? (
          <div className="card emptyState">
            계정별 포트폴리오를 확인하려면 <Link className="inlineLink" href="/login">로그인</Link>해 주세요.
          </div>
        ) : portfolioResult.error || !portfolioResult.summary ? (
          <ApiMessage title="포트폴리오를 불러오지 못했습니다" message={portfolioResult.error ?? "알 수 없는 오류가 발생했습니다."} />
        ) : (
          <div className="statsGrid">
            <div className="card stat"><span className="muted">보유 종목</span><strong>{portfolioResult.summary.positionsCount}</strong></div>
            {portfolioResult.summary.currencies.map((item) => (
              <div className="card stat" key={item.currency}>
                <span className="muted">미실현 손익 · {item.currency}</span>
                <strong>{item.unrealizedPnl.toLocaleString("ko-KR")}</strong>
              </div>
            ))}
            {portfolioResult.summary.currencies.length === 0 && (
              <div className="card stat"><span className="muted">포트폴리오 상태</span><strong>거래 없음</strong></div>
            )}
          </div>
        )}
      </section>

      <section>
        <h2>오늘 확인할 것</h2>
        <div className="card">
          <h3>시장 요인과 기업 요인을 분리해서 확인</h3>
          <p className="muted">가격이 크게 움직여도 곧바로 기업 고유 위험으로 판단하지 않습니다. 시장 → 산업 → 기업 순서로 원인을 검토합니다.</p>
        </div>
      </section>
    </div>
  );
}
