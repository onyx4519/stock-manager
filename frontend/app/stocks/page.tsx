import Link from "next/link";
import { ApiMessage } from "@/components/ApiMessage";
import { DataBadge } from "@/components/DataBadge";
import { getQuotes } from "@/lib/api";

export default async function StocksPage() {
  const result = await getQuotes()
    .then((quotes) => ({ quotes, error: null }))
    .catch((error: Error) => ({ quotes: [], error: error.message }));

  return <div className="page"><div className="pageHeader"><div><div className="eyebrow">Stocks</div><h1>추적 종목</h1></div></div>{result.error ? <ApiMessage title="종목을 불러오지 못했습니다" message={result.error} /> : result.quotes.length === 0 ? <ApiMessage title="추적 중인 종목이 없습니다" message="MASSIVE_SYMBOLS에 종목을 추가해 주세요." /> : <div className="list">{result.quotes.map(q => <Link className="card listItem" key={q.symbol} href={`/stocks/${q.symbol}`}><div><strong>{q.companyName}</strong><div className="muted">{q.symbol} · {q.currency}</div></div><DataBadge status={q.dataStatus}/></Link>)}</div>}</div>;
}
