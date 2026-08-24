"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { deleteWatchlistAction } from "@/app/watchlist/actions";
import { DataBadge } from "@/components/DataBadge";
import type { WatchlistItem } from "@/types/market";


const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(value);


export function WatchlistManager({ items }: { items: WatchlistItem[] }) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [message, setMessage] = useState<string | null>(null);

  const removeItem = (symbol: string) => {
    setMessage(null);
    startTransition(async () => {
      const result = await deleteWatchlistAction(symbol);
      if (!result.ok) {
        setMessage(result.message ?? "관심종목을 삭제하지 못했습니다.");
        return;
      }
      router.refresh();
    });
  };

  if (items.length === 0) {
    return (
      <div className="card emptyState">
        저장된 관심종목이 없습니다. <Link className="inlineLink" href="/stocks">종목 검색에서 추가하기</Link>
      </div>
    );
  }

  return (
    <>
      {message && <div className="card formMessage" role="alert">{message}</div>}
      <div className="watchlistGrid">
        {items.map((item) => (
          <article className="card watchlistCard" key={item.symbol}>
            <div className="rowBetween gap">
              <div>
                <Link href={`/stocks/${item.symbol}`}><strong>{item.companyName}</strong></Link>
                <div className="muted">{item.symbol} · {item.currency}</div>
              </div>
              <DataBadge status={item.dataStatus} />
            </div>
            {item.price === null ? (
              <p className="muted">현재 시세를 불러올 수 없습니다.</p>
            ) : (
              <div className="watchlistPrice">
                <b>{money(item.price, item.currency)}</b>
                {item.changePercent !== null && (
                  <span className={item.changePercent >= 0 ? "positive" : "negative"}>
                    {item.changePercent >= 0 ? "+" : ""}{item.changePercent.toFixed(2)}%
                  </span>
                )}
              </div>
            )}
            <div className="rowBetween gap">
              <span className="meta">추가 {new Date(item.createdAt).toLocaleDateString("ko-KR")}</span>
              <button
                className="dangerButton"
                disabled={isPending}
                onClick={() => removeItem(item.symbol)}
                type="button"
              >
                삭제
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}
