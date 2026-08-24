import { ApiMessage } from "@/components/ApiMessage";
import { RecentStocks } from "@/components/RecentStocks";
import { StockSearchResults } from "@/components/StockSearchResults";
import { getCurrentUser, getWatchlist, searchStocks } from "@/lib/api";


export default async function StocksPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string | string[] }>;
}) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q.trim() : "";
  const [searchResult, watchlistResult, currentUser] = await Promise.all([
    searchStocks(query)
      .then((search) => ({ search, error: null }))
      .catch((error: Error) => ({ search: null, error: error.message })),
    getWatchlist().catch(() => []),
    getCurrentUser().catch(() => null),
  ]);
  const result = {
    search: searchResult.search,
    watchlist: watchlistResult,
    error: searchResult.error,
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Stocks</div>
          <h1>종목 검색</h1>
          <p className="muted">국내 기업의 한글·영문명과 미국 종목의 한글 별칭·영문명·티커로 검색할 수 있습니다.</p>
        </div>
      </div>

      <form action="/stocks" className="card stockSearchForm">
        <label htmlFor="stock-search">기업명·티커·종목코드</label>
        <div className="stockSearchControls">
          <input
            defaultValue={query}
            id="stock-search"
            name="q"
            placeholder="예: 삼성전자, Samsung Electronics, 조비 에비에이션, JOBY"
            type="search"
          />
          <button className="primaryButton" type="submit">검색</button>
        </div>
      </form>

      {currentUser && <RecentStocks userId={currentUser.id} />}

      <section>
        <div className="rowBetween gap sectionTitleRow">
          <h2>{query ? `‘${query}’ 전체 시장 검색 결과` : "주요 종목"}</h2>
          {result.search && <span className="muted">{result.search.totalCount}개</span>}
        </div>
        {!query && (
          <p className="searchNotice">시장 탐색을 위한 국내·미국 주요 종목이며 투자 추천을 의미하지 않습니다.</p>
        )}
        {result.error ? (
          <ApiMessage title="종목을 불러오지 못했습니다" message={result.error} />
        ) : (
          <>
            {result.search?.warnings.map((warning) => (
              <p className="searchNotice" key={warning}>{warning}</p>
            ))}
            <StockSearchResults
              canSave={currentUser !== null}
              items={result.search?.items ?? []}
              watchedSymbols={result.watchlist.map((item) => item.symbol)}
            />
          </>
        )}
      </section>
    </div>
  );
}
