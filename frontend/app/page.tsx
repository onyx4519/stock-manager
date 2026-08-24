import { QuoteCard } from "@/components/QuoteCard";
import { ApiMessage } from "@/components/ApiMessage";
import { getQuotes } from "@/lib/api";
import { mockPortfolio } from "@/lib/mockPortfolio";

export default async function DashboardPage() {
  const quoteResult = await getQuotes()
    .then((quotes) => ({ quotes, error: null }))
    .catch((error: Error) => ({ quotes: [], error: error.message }));
  const totalPnl = mockPortfolio.reduce((sum, item) => sum + item.unrealizedPnl, 0);
  return (
    <div className="page">
      <div className="pageHeader">
        <div><div className="eyebrow">Dashboard</div><h1>오늘의 투자 현황</h1></div>
        <p className="muted">시세는 백엔드 Provider 기준이며 포트폴리오는 아직 Mock 데이터입니다.</p>
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
        <div className="statsGrid">
          <div className="card stat"><span className="muted">보유 종목</span><strong>{mockPortfolio.length}</strong></div>
          <div className="card stat"><span className="muted">미실현 손익(통화 혼합 예시)</span><strong>{totalPnl.toLocaleString("ko-KR")}</strong></div>
          <div className="card stat"><span className="muted">포트폴리오 상태</span><strong>MOCK</strong></div>
        </div>
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
