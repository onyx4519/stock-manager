import { ApiMessage } from "@/components/ApiMessage";
import { StockSearchResults } from "@/components/StockSearchResults";
import { getWatchlist, searchStocks } from "@/lib/api";


export default async function StocksPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string | string[] }>;
}) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q.trim() : "";
  const result = await Promise.all([searchStocks(query), getWatchlist()])
    .then(([quotes, watchlist]) => ({ quotes, watchlist, error: null }))
    .catch((error: Error) => ({ quotes: [], watchlist: [], error: error.message }));

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Stocks</div>
          <h1>종목 검색</h1>
          <p className="muted">현재 연결된 KIS·Massive 종목에서 검색하고 관심종목으로 저장합니다.</p>
        </div>
      </div>

      <form action="/stocks" className="card stockSearchForm">
        <label htmlFor="stock-search">기업명·티커·종목코드</label>
        <div className="stockSearchControls">
          <input
            defaultValue={query}
            id="stock-search"
            name="q"
            placeholder="예: 삼성전자, 005930, NVDA"
            type="search"
          />
          <button className="primaryButton" type="submit">검색</button>
        </div>
      </form>

      <section>
        <div className="rowBetween gap sectionTitleRow">
          <h2>{query ? `‘${query}’ 검색 결과` : "연결된 종목"}</h2>
          {!result.error && <span className="muted">{result.quotes.length}개</span>}
        </div>
        {result.error ? (
          <ApiMessage title="종목을 불러오지 못했습니다" message={result.error} />
        ) : (
          <StockSearchResults
            quotes={result.quotes}
            watchedSymbols={result.watchlist.map((item) => item.symbol)}
          />
        )}
      </section>
    </div>
  );
}
