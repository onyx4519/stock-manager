import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { cache } from "react";
import { ApiMessage } from "@/components/ApiMessage";
import { DataBadge } from "@/components/DataBadge";
import {
  DartDisclosureSection,
  DartFinancialSection,
} from "@/components/DartSections";
import {
  ApiError,
  getDartDisclosures,
  getDartFinancials,
  getQuote,
} from "@/lib/api";


const getStockQuote = cache(getQuote);


export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const quote = await getStockQuote(symbol).catch(() => null);
  const title = quote ? `${quote.companyName} (${quote.symbol})` : `종목 ${symbol}`;
  const description = quote
    ? `${quote.companyName}의 EOD 시세와 OpenDART 재무·공시 정보입니다.`
    : "종목 시세와 재무·공시 정보입니다.";
  return {
    title,
    description,
    openGraph: { title, description, images: [] },
    twitter: { title, description, images: [] },
  };
}


async function capture<T>(promise: Promise<T>) {
  try {
    return { data: await promise, error: null };
  } catch (error) {
    return { data: null, error: error instanceof Error ? error : new Error("알 수 없는 오류가 발생했습니다.") };
  }
}


function dartErrorMessage(error: Error | null) {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 404) return "OpenDART 기업 정보를 찾을 수 없습니다.";
  if (error instanceof ApiError && error.status === 503) return "OpenDART API 설정을 확인해 주세요.";
  return "OpenDART 데이터를 불러오지 못했습니다.";
}

export default async function StockDetailPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  const isDomestic = /^\d{6}$/.test(symbol);
  const previousBusinessYear = new Date().getFullYear() - 1;
  const [quoteResult, disclosuresResult, financialsResult] = await Promise.all([
    capture(getStockQuote(symbol)),
    isDomestic ? capture(getDartDisclosures(symbol, 365, 10)) : Promise.resolve({ data: null, error: null }),
    isDomestic ? capture(getDartFinancials(symbol, previousBusinessYear, "11011")) : Promise.resolve({ data: null, error: null }),
  ]);

  if (quoteResult.error instanceof ApiError && quoteResult.error.status === 404) return notFound();
  if (!quoteResult.data) {
    return <div className="page"><ApiMessage title="종목 정보를 불러오지 못했습니다" message={quoteResult.error?.message ?? "알 수 없는 오류가 발생했습니다."} /></div>;
  }
  const quote = quoteResult.data;
  const dartCompany = disclosuresResult.data?.company ?? financialsResult.data?.company ?? null;

  return <div className="page">
    <div className="pageHeader"><div><div className="eyebrow">{quote.symbol}</div><h1>{quote.companyName}</h1></div><DataBadge status={quote.dataStatus}/></div>
    <div className="grid2">
      <div className="card"><div className="muted">현재가</div><div className="price">{quote.price.toLocaleString("ko-KR")} {quote.currency}</div><div className="meta">{new Date(quote.timestamp).toLocaleString("ko-KR")} · {quote.provider}</div></div>
      <div className="card companySummary"><h3>기업 정보</h3>{dartCompany ? <><strong>{dartCompany.corporationName}</strong>{dartCompany.corporationEnglishName && <p className="muted">{dartCompany.corporationEnglishName}</p>}<div className="meta">OpenDART 고유번호 {dartCompany.corporationCode}</div></> : <p className="muted">{isDomestic ? "OpenDART 기업 정보를 불러오지 못했습니다." : "미국 종목 기업정보는 향후 SEC·기업 IR 데이터로 연결합니다."}</p>}</div>
    </div>
    {isDomestic ? <>
      <DartFinancialSection data={financialsResult.data} error={dartErrorMessage(financialsResult.error)} />
      <DartDisclosureSection data={disclosuresResult.data} error={dartErrorMessage(disclosuresResult.error)} />
    </> : <div className="card emptyState">OpenDART 재무·공시는 국내 6자리 종목에만 제공됩니다.</div>}
    <div className="card"><h3>데이터 해석 주의</h3><p className="muted">시세는 EOD 기준이며 재무정보는 제출인이 공시한 원문을 표시합니다. 이 화면은 투자 판단이나 수익을 보장하지 않습니다.</p></div>
  </div>;
}
