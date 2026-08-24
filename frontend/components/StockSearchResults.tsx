"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { addWatchlistAction } from "@/app/watchlist/actions";
import { DataBadge } from "@/components/DataBadge";
import type { StockSearchItem } from "@/types/market";


const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(value);


export function StockSearchResults({
  canSave,
  items,
  watchedSymbols,
}: {
  canSave: boolean;
  items: StockSearchItem[];
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

  if (items.length === 0) {
    return <div className="card emptyState">검색 결과가 없습니다.</div>;
  }

  return (
    <>
      {message && <div className="card formMessage" role="alert">{message}</div>}
      <div className="stockResultList">
        {items.map((item) => {
          const isWatched = watched.has(item.symbol);
          return (
            <article className="card stockResultRow" key={item.symbol}>
              <Link className="stockResultLink" href={`/stocks/${item.symbol}`}>
                <div>
                  <strong>{item.companyName}</strong>
                  <div className="muted">
                    {item.symbol} · {item.market} · {item.currency} · {item.provider}
                  </div>
                </div>
                <div className="stockResultPrice">
                  {item.price !== null && item.changePercent !== null ? (
                    <>
                      <b>{money(item.price, item.currency)}</b>
                      <span className={item.changePercent >= 0 ? "positive" : "negative"}>
                        {item.changePercent >= 0 ? "+" : ""}{item.changePercent.toFixed(2)}%
                      </span>
                      <DataBadge status={item.dataStatus} />
                    </>
                  ) : (
                    <span className="muted">선택하면 시세 조회</span>
                  )}
                </div>
              </Link>
              {canSave ? (
                <button
                  className="secondaryButton watchButton"
                  disabled={isPending || isWatched}
                  onClick={() => addItem(item.symbol)}
                  type="button"
                >
                  {isWatched ? "저장됨" : pendingSymbol === item.symbol ? "추가 중" : "+ 관심종목"}
                </button>
              ) : (
                <Link className="secondaryButton watchButton loginWatchButton" href="/login">
                  로그인 후 저장
                </Link>
              )}
            </article>
          );
        })}
      </div>
    </>
  );
}
