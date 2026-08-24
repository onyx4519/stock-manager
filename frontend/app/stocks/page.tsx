import Link from "next/link";
import { mockQuotes } from "@/lib/mockData";
import { DataBadge } from "@/components/DataBadge";

export default function StocksPage() {
  return <div className="page"><div className="pageHeader"><div><div className="eyebrow">Stocks</div><h1>종목 검색</h1></div></div><div className="list">{mockQuotes.map(q => <Link className="card listItem" key={q.symbol} href={`/stocks/${q.symbol}`}><div><strong>{q.companyName}</strong><div className="muted">{q.symbol} · {q.currency}</div></div><DataBadge status={q.dataStatus}/></Link>)}</div></div>;
}
