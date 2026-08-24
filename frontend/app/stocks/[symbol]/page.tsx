import { notFound } from "next/navigation";
import { ApiMessage } from "@/components/ApiMessage";
import { DataBadge } from "@/components/DataBadge";
import { ApiError, getQuote } from "@/lib/api";

export default async function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const result = await getQuote(symbol)
    .then((quote) => ({ quote, error: null }))
    .catch((error: Error) => ({ quote: null, error }));
  if (result.error instanceof ApiError && result.error.status === 404) return notFound();
  if (!result.quote) {
    return <div className="page"><ApiMessage title="종목 정보를 불러오지 못했습니다" message={result.error?.message ?? "알 수 없는 오류가 발생했습니다."} /></div>;
  }
  const quote = result.quote;
  return <div className="page">
    <div className="pageHeader"><div><div className="eyebrow">{quote.symbol}</div><h1>{quote.companyName}</h1></div><DataBadge status={quote.dataStatus}/></div>
    <div className="grid2">
      <div className="card"><div className="muted">현재가</div><div className="price">{quote.price.toLocaleString("ko-KR")} {quote.currency}</div><div className="meta">{new Date(quote.timestamp).toLocaleString("ko-KR")} · {quote.provider}</div></div>
      <div className="card"><h3>기업 한눈에 보기</h3><p className="muted">실제 기업 설명, 산업, 핵심 사업 정보는 OpenDART/SEC/기업 IR 연결 후 표시합니다.</p></div>
    </div>
    <div className="tabRow"><button>개요</button><button>실적</button><button>재무</button><button>뉴스</button><button>위험</button><button>투자분석</button></div>
    <div className="card"><h3>분석 상태</h3><p className="muted">현재 가격은 EOD 데이터이며, 재무·공시·뉴스가 연결되기 전에는 투자 판단을 생성하지 않습니다.</p></div>
  </div>;
}
