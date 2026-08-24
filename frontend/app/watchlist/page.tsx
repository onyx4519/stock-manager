import { ApiMessage } from "@/components/ApiMessage";
import { WatchlistManager } from "@/components/WatchlistManager";
import { getWatchlist } from "@/lib/api";


export default async function WatchlistPage() {
  const result = await getWatchlist()
    .then((items) => ({ items, error: null }))
    .catch((error: Error) => ({ items: [], error: error.message }));

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Watchlist</div>
          <h1>관심종목</h1>
          <p className="muted">저장한 종목의 최근 EOD 시세를 한곳에서 확인합니다.</p>
        </div>
        {!result.error && <div className="countBadge">{result.items.length}개 저장</div>}
      </div>
      {result.error ? (
        <ApiMessage title="관심종목을 불러오지 못했습니다" message={result.error} />
      ) : (
        <WatchlistManager items={result.items} />
      )}
    </div>
  );
}
