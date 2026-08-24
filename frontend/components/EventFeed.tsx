"use client";

import { useMemo, useState } from "react";
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


function normalizeSearchText(value: string) {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("ko-KR")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}


function editDistance(left: string, right: string) {
  const previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  for (let leftIndex = 1; leftIndex <= left.length; leftIndex += 1) {
    const current = [leftIndex];
    for (let rightIndex = 1; rightIndex <= right.length; rightIndex += 1) {
      const substitutionCost = left[leftIndex - 1] === right[rightIndex - 1] ? 0 : 1;
      current[rightIndex] = Math.min(
        current[rightIndex - 1] + 1,
        previous[rightIndex] + 1,
        previous[rightIndex - 1] + substitutionCost,
      );
    }
    previous.splice(0, previous.length, ...current);
  }
  return previous[right.length];
}


function keywordMatches(keyword: string, searchableText: string, words: string[]) {
  if (searchableText.includes(keyword)) return true;
  if (keyword.length < 3) return false;

  const allowedDistance = keyword.length >= 6 ? 2 : 1;
  return words.some((word) => (
    Math.abs(word.length - keyword.length) <= allowedDistance
    && editDistance(keyword, word) <= allowedDistance
  ));
}


function eventMatches(event: UnifiedEvent, query: string) {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return true;

  const searchableText = normalizeSearchText([
    event.type === "news" ? "뉴스" : "공시",
    event.title,
    event.description ?? "",
    event.source,
    ...event.symbols,
  ].join(" "));
  const words = searchableText.split(" ").filter(Boolean);
  return normalizedQuery
    .split(" ")
    .filter(Boolean)
    .every((keyword) => keywordMatches(keyword, searchableText, words));
}


export function EventFeed({
  news,
  disclosures,
}: {
  news: NewsArticle[];
  disclosures: DartDisclosure[];
}) {
  const [query, setQuery] = useState("");
  const events = useMemo(
    () => [
      ...news.map(toNewsEvent),
      ...disclosures.map(toDisclosureEvent),
    ].sort(
      (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime(),
    ),
    [news, disclosures],
  );
  const filteredEvents = useMemo(
    () => events.filter((event) => eventMatches(event, query)),
    [events, query],
  );

  if (events.length === 0) {
    return <div className="card emptyState">표시할 최근 뉴스나 공시가 없습니다.</div>;
  }

  return (
    <section className="eventFeedSection" aria-label="뉴스 및 공시 검색 결과">
      <div className="card eventSearchPanel">
        <label htmlFor="eventKeywordSearch">이벤트 키워드 검색</label>
        <div className="eventSearchControl">
          <span className="eventSearchIcon" aria-hidden="true" />
          <input
            id="eventKeywordSearch"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="기업명, 종목코드, 뉴스·공시 키워드를 입력하세요"
            autoComplete="off"
          />
          {query && (
            <button type="button" onClick={() => setQuery("")}>
              초기화
            </button>
          )}
        </div>
        <p aria-live="polite">
          {query.trim()
            ? `일치하거나 유사한 이벤트 ${filteredEvents.length}건`
            : `최근 이벤트 ${events.length}건을 검색할 수 있습니다.`}
        </p>
      </div>

      {filteredEvents.length > 0 ? (
        <div className="eventList">
          {filteredEvents.map((event) => (
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
      ) : (
        <div className="card emptyState eventSearchEmpty">
          입력한 키워드와 일치하거나 유사한 뉴스·공시가 없습니다.
        </div>
      )}
    </section>
  );
}
