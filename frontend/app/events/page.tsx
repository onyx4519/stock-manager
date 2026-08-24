import { ApiMessage } from "@/components/ApiMessage";
import { EventFeed } from "@/components/EventFeed";
import { getDartDisclosures, getNews, getQuotes } from "@/lib/api";
import type { DartDisclosure } from "@/types/market";


function errorMessage(result: PromiseSettledResult<unknown>) {
  if (result.status === "fulfilled") return null;
  return result.reason instanceof Error ? result.reason.message : "알 수 없는 오류가 발생했습니다.";
}


export default async function EventsPage() {
  const [quotesResult, newsResult] = await Promise.allSettled([
    getQuotes(),
    getNews(undefined, 30),
  ]);
  const quotes = quotesResult.status === "fulfilled" ? quotesResult.value : [];
  const news = newsResult.status === "fulfilled" ? newsResult.value.items : [];
  const domesticSymbols = quotes
    .map((quote) => quote.symbol)
    .filter((symbol) => /^\d{6}$/.test(symbol));
  const disclosureResults = await Promise.allSettled(
    domesticSymbols.map((symbol) => getDartDisclosures(symbol, 180, 20)),
  );
  const disclosures: DartDisclosure[] = disclosureResults
    .flatMap((result) => result.status === "fulfilled" ? result.value.items : [])
    .filter((item, index, items) => items.findIndex((candidate) => candidate.receiptNumber === item.receiptNumber) === index);
  const disclosureFailed = domesticSymbols.length > 0
    && disclosureResults.every((result) => result.status === "rejected");

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Events</div>
          <h1>뉴스·공시 이벤트</h1>
          <p className="muted">미국 종목 뉴스와 국내 종목 공시를 날짜순으로 함께 확인합니다.</p>
        </div>
        <span className="sourceBadge">Massive 뉴스 · OpenDART 공시</span>
      </div>
      <div className="statsGrid eventStats">
        <div className="card stat"><span className="muted">미국 뉴스</span><strong>{news.length}</strong></div>
        <div className="card stat"><span className="muted">국내 공시</span><strong>{disclosures.length}</strong></div>
        <div className="card stat"><span className="muted">전체 이벤트</span><strong>{news.length + disclosures.length}</strong></div>
      </div>
      {newsResult.status === "rejected" && (
        <ApiMessage title="Massive 뉴스를 불러오지 못했습니다" message={errorMessage(newsResult) ?? "API 상태를 확인해 주세요."} />
      )}
      {quotesResult.status === "rejected" && (
        <ApiMessage title="국내 공시 대상 종목을 불러오지 못했습니다" message={errorMessage(quotesResult) ?? "시세 API 상태를 확인해 주세요."} />
      )}
      {disclosureFailed && (
        <ApiMessage title="OpenDART 공시를 불러오지 못했습니다" message="API 설정 또는 OpenDART 서비스 상태를 확인해 주세요." />
      )}
      <EventFeed news={news} disclosures={disclosures} />
    </div>
  );
}
