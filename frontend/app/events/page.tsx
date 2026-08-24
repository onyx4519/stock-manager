import { ApiMessage } from "@/components/ApiMessage";
import { DisclosureItems } from "@/components/DartSections";
import { getDartDisclosures, getQuotes } from "@/lib/api";
import type { DartDisclosure } from "@/types/market";


export default async function EventsPage() {
  const quotesResult = await getQuotes()
    .then((quotes) => ({ quotes, error: null }))
    .catch((error: Error) => ({ quotes: [], error: error.message }));

  if (quotesResult.error) {
    return <div className="page"><ApiMessage title="공시 대상 종목을 불러오지 못했습니다" message={quotesResult.error} /></div>;
  }

  const domesticSymbols = quotesResult.quotes
    .map((quote) => quote.symbol)
    .filter((symbol) => /^\d{6}$/.test(symbol));
  const disclosureResults = await Promise.allSettled(
    domesticSymbols.map((symbol) => getDartDisclosures(symbol, 180, 20)),
  );
  const disclosures: DartDisclosure[] = disclosureResults
    .flatMap((result) => result.status === "fulfilled" ? result.value.items : [])
    .filter((item, index, items) => items.findIndex((candidate) => candidate.receiptNumber === item.receiptNumber) === index)
    .sort((a, b) => b.receiptDate.localeCompare(a.receiptDate));
  const allFailed = domesticSymbols.length > 0 && disclosureResults.every((result) => result.status === "rejected");

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Events</div>
          <h1>공시·이벤트</h1>
          <p className="muted">연결된 국내 종목의 최근 OpenDART 공시를 모아봅니다.</p>
        </div>
        <span className="sourceBadge">OpenDART · 최근 180일</span>
      </div>
      {domesticSymbols.length === 0 ? (
        <div className="card emptyState">연결된 국내 종목이 없습니다.</div>
      ) : allFailed ? (
        <ApiMessage title="OpenDART 공시를 불러오지 못했습니다" message="API 설정 또는 OpenDART 서비스 상태를 확인해 주세요." />
      ) : (
        <DisclosureItems items={disclosures} />
      )}
    </div>
  );
}
