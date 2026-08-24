import { ApiMessage } from "@/components/ApiMessage";
import { QuoteCard } from "@/components/QuoteCard";
import { getQuotes } from "@/lib/api";

export default async function MarketPage() {
  const result = await getQuotes()
    .then((quotes) => ({ quotes, error: null }))
    .catch((error: Error) => ({ quotes: [], error: error.message }));

  return <div className="page"><div className="pageHeader"><div><div className="eyebrow">Market</div><h1>시장 대시보드</h1></div><p className="muted">최근 완료 거래일 기준</p></div>{result.error ? <ApiMessage title="시장 데이터를 불러오지 못했습니다" message={result.error} /> : result.quotes.length === 0 ? <ApiMessage title="표시할 시세가 없습니다" message="백엔드 종목 설정을 확인해 주세요." /> : <div className="grid2">{result.quotes.map((quote) => <QuoteCard key={quote.symbol} quote={quote} />)}</div>}<div className="card"><h3>데이터 기준</h3><p className="muted">미국 종목은 Massive, 국내 종목은 KIS에서 가져온 EOD 데이터입니다. 지수·환율·경제일정은 이후 단계에서 연결합니다.</p></div></div>;
}
