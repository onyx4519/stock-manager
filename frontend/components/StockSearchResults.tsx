"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { addWatchlistAction } from "@/app/watchlist/actions";
import { DataBadge } from "@/components/DataBadge";
import type { StockQuote } from "@/types/market";


const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(value);


export function StockSearchResults({
  quotes,
  watchedSymbols,
}: {
  quotes: StockQuote[];
  watchedSymbols: string[];
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [pendingSymbol, setPendingSymbol] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const watched = new Set(watchedSymbols);

  const addItem = (symbol: string) => {
    setMessage(null);
    setPendingSymbol(symbol);
    startTransition(async () => {
      const result = await addWatchlistAction(symbol);
      setPendingSymbol(null);
      if (!result.ok) {
        setMessage(result.message ?? "관심종목을 추가하지 못했습니다.");
        return;
      }
      router.refresh();
    });
  };

  if (quotes.length === 0) {
    return <div className="card emptyState">검색 결과가 없습니다.</div>;
  }

  return (
    <>
      {message && <div className="card formMessage" role="alert">{message}</div>}
      <div className="stockResultList">
        {quotes.map((quote) => {
          const isWatched = watched.has(quote.symbol);
          return (
            <article className="card stockResultRow" key={quote.symbol}>
              <Link className="stockResultLink" href={`/stocks/${quote.symbol}`}>
                <div>
                  <strong>{quote.companyName}</strong>
                  <div className="muted">{quote.symbol} · {quote.currency} · {quote.provider}</div>
                </div>
                <div className="stockResultPrice">
                  <b>{money(quote.price, quote.currency)}</b>
                  <span className={quote.changePercent >= 0 ? "positive" : "negative"}>
                    {quote.changePercent >= 0 ? "+" : ""}{quote.changePercent.toFixed(2)}%
                  </span>
                  <DataBadge status={quote.dataStatus} />
                </div>
              </Link>
              <button
                className="secondaryButton watchButton"
                disabled={isPending || isWatched}
                onClick={() => addItem(quote.symbol)}
                type="button"
              >
                {isWatched ? "저장됨" : pendingSymbol === quote.symbol ? "추가 중" : "+ 관심종목"}
              </button>
            </article>
          );
        })}
      </div>
    </>
  );
}
