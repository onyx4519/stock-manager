import { QuoteCard } from "@/components/QuoteCard";
import { mockPortfolio, mockQuotes } from "@/lib/mockData";

export default function DashboardPage() {
  const totalPnl = mockPortfolio.reduce((sum, item) => sum + item.unrealizedPnl, 0);
  return (
    <div className="page">
      <div className="pageHeader">
        <div><div className="eyebrow">Dashboard</div><h1>오늘의 투자 현황</h1></div>
        <p className="muted">현재 화면의 숫자는 기능 검증용 Mock 데이터입니다.</p>
      </div>

      <section>
        <h2>시장·관심 시세</h2>
        <div className="grid2">{mockQuotes.map(q => <QuoteCard key={q.symbol} quote={q} />)}</div>
      </section>

      <section>
        <h2>내 포트폴리오</h2>
        <div className="statsGrid">
          <div className="card stat"><span className="muted">보유 종목</span><strong>{mockPortfolio.length}</strong></div>
          <div className="card stat"><span className="muted">미실현 손익(통화 혼합 예시)</span><strong>{totalPnl.toLocaleString("ko-KR")}</strong></div>
          <div className="card stat"><span className="muted">데이터 상태</span><strong>MOCK</strong></div>
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
