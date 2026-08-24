import type { NewsArticle, NewsFeed } from "@/types/market";


function NewsItems({ items }: { items: NewsArticle[] }) {
  if (items.length === 0) {
    return <div className="card emptyState">최근 뉴스가 없습니다.</div>;
  }

  return (
    <div className="eventList">
      {items.map((item) => (
        <a
          className="card eventRow"
          href={item.articleUrl}
          key={item.id}
          rel="noreferrer"
          target="_blank"
        >
          <div className="eventBody">
            <div className="eventLabelRow">
              <span className="eventType eventTypeNews">뉴스</span>
              {item.tickers.map((ticker) => (
                <span className="tickerTag" key={ticker}>{ticker}</span>
              ))}
            </div>
            <strong>{item.title}</strong>
            {item.description && <p className="eventDescription">{item.description}</p>}
            <div className="meta">
              {item.publisherName}{item.author ? ` · ${item.author}` : ""}
            </div>
          </div>
          <div className="eventMeta">
            <span>{new Date(item.publishedAt).toLocaleString("ko-KR")}</span>
            <span className="externalMark">기사 원문</span>
          </div>
        </a>
      ))}
    </div>
  );
}


export function NewsSection({
  data,
  error,
}: {
  data: NewsFeed | null;
  error: string | null;
}) {
  return (
    <section>
      <div className="rowBetween gap sectionTitleRow">
        <h2>최근 뉴스</h2>
        {data && <span className="sourceBadge">Massive · {data.symbols.join(", ")}</span>}
      </div>
      {error ? (
        <div className="card emptyState">{error}</div>
      ) : (
        <NewsItems items={data?.items ?? []} />
      )}
    </section>
  );
}
