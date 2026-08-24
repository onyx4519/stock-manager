import type { DartDisclosure, NewsArticle } from "@/types/market";


type UnifiedEvent = {
  id: string;
  type: "news" | "disclosure";
  title: string;
  description: string | null;
  source: string;
  symbols: string[];
  occurredAt: string;
  url: string;
};


function toNewsEvent(item: NewsArticle): UnifiedEvent {
  return {
    id: `news-${item.id}`,
    type: "news",
    title: item.title,
    description: item.description,
    source: item.publisherName,
    symbols: item.tickers,
    occurredAt: item.publishedAt,
    url: item.articleUrl,
  };
}


function toDisclosureEvent(item: DartDisclosure): UnifiedEvent {
  return {
    id: `dart-${item.receiptNumber}`,
    type: "disclosure",
    title: item.reportName,
    description: item.remarks ? `공시 비고: ${item.remarks}` : null,
    source: `${item.corporationName} · 제출인 ${item.filerName}`,
    symbols: item.stockCode ? [item.stockCode] : [],
    occurredAt: `${item.receiptDate}T00:00:00+09:00`,
    url: item.viewerUrl,
  };
}


export function EventFeed({
  news,
  disclosures,
}: {
  news: NewsArticle[];
  disclosures: DartDisclosure[];
}) {
  const events = [
    ...news.map(toNewsEvent),
    ...disclosures.map(toDisclosureEvent),
  ].sort(
    (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime(),
  );

  if (events.length === 0) {
    return <div className="card emptyState">표시할 최근 뉴스나 공시가 없습니다.</div>;
  }

  return (
    <div className="eventList">
      {events.map((event) => (
        <a
          className="card eventRow"
          href={event.url}
          key={event.id}
          rel="noreferrer"
          target="_blank"
        >
          <div className="eventBody">
            <div className="eventLabelRow">
              <span className={`eventType eventType${event.type === "news" ? "News" : "Disclosure"}`}>
                {event.type === "news" ? "뉴스" : "공시"}
              </span>
              {event.symbols.map((symbol) => (
                <span className="tickerTag" key={symbol}>{symbol}</span>
              ))}
            </div>
            <strong>{event.title}</strong>
            {event.description && <p className="eventDescription">{event.description}</p>}
            <div className="meta">{event.source}</div>
          </div>
          <div className="eventMeta">
            <span>{new Date(event.occurredAt).toLocaleString("ko-KR")}</span>
            <span className="externalMark">
              {event.type === "news" ? "기사 원문" : "DART 원문"}
            </span>
          </div>
        </a>
      ))}
    </div>
  );
}
