import { notFound } from "next/navigation";
import { mockQuotes } from "@/lib/mockData";
import { DataBadge } from "@/components/DataBadge";

export default async function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const quote = mockQuotes.find(q => q.symbol === symbol);
  if (!quote) return notFound();
  return <div className="page">
    <div className="pageHeader"><div><div className="eyebrow">{quote.symbol}</div><h1>{quote.companyName}</h1></div><DataBadge status={quote.dataStatus}/></div>
    <div className="grid2">
      <div className="card"><div className="muted">현재가</div><div className="price">{quote.price.toLocaleString("ko-KR")} {quote.currency}</div><div className="meta">{new Date(quote.timestamp).toLocaleString("ko-KR")} · {quote.provider}</div></div>
      <div className="card"><h3>기업 한눈에 보기</h3><p className="muted">실제 기업 설명, 산업, 핵심 사업 정보는 OpenDART/SEC/기업 IR 연결 후 표시합니다.</p></div>
    </div>
    <div className="tabRow"><button>개요</button><button>실적</button><button>재무</button><button>뉴스</button><button>위험</button><button>투자분석</button></div>
    <div className="card"><h3>분석 상태</h3><p className="muted">현재는 Mock 데이터이므로 실제 투자 판단을 생성하지 않습니다.</p></div>
  </div>;
}
