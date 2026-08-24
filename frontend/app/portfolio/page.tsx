import { mockPortfolio } from "@/lib/mockPortfolio";

export default function PortfolioPage() {
  return <div className="page"><div className="pageHeader"><div><div className="eyebrow">Portfolio</div><h1>내 포트폴리오</h1><p className="muted">데이터베이스 연결 전 Mock 포트폴리오입니다.</p></div><button className="primaryButton">+ 거래 추가</button></div><div className="portfolioList">{mockPortfolio.map(p => <article className="card positionCard" key={p.symbol}><div><strong>{p.companyName}</strong><div className="muted">{p.symbol}</div></div><div className="positionMetrics"><span>수량 <b>{p.quantity}</b></span><span>평균단가 <b>{p.averageCost.toLocaleString("ko-KR")}</b></span><span>현재가 <b>{p.currentPrice.toLocaleString("ko-KR")}</b></span><span>미실현손익 <b>{p.unrealizedPnl.toLocaleString("ko-KR")}</b></span><span>비중 <b>{p.weightPercent.toFixed(1)}%</b></span></div></article>)}</div></div>;
}
