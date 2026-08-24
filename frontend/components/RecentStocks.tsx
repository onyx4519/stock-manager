"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";


type RecentStock = {
  companyName: string;
  currency: string;
  symbol: string;
  viewedAt: string;
};


const MAX_STORED_ITEMS = 10;
const MAX_VISIBLE_ITEMS = 5;
const UPDATE_EVENT = "stock-manager:recent-stocks-updated";


function storageKey(userId: string) {
  return `stock-manager:recent-stocks:${userId}`;
}


function isRecentStock(value: unknown): value is RecentStock {
  if (!value || typeof value !== "object") return false;
  const item = value as Partial<RecentStock>;
  return (
    typeof item.companyName === "string" &&
    typeof item.currency === "string" &&
    typeof item.symbol === "string" &&
    typeof item.viewedAt === "string" &&
    Number.isFinite(Date.parse(item.viewedAt))
  );
}


function readRecentStocks(userId: string): RecentStock[] {
  try {
    const value = window.localStorage.getItem(storageKey(userId));
    if (!value) return [];
    const parsed: unknown = JSON.parse(value);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(isRecentStock)
      .sort((left, right) => Date.parse(right.viewedAt) - Date.parse(left.viewedAt))
      .slice(0, MAX_STORED_ITEMS);
  } catch {
    return [];
  }
}


function saveRecentStocks(userId: string, items: RecentStock[]) {
  window.localStorage.setItem(
    storageKey(userId),
    JSON.stringify(items.slice(0, MAX_STORED_ITEMS)),
  );
  window.dispatchEvent(new CustomEvent(UPDATE_EVENT, { detail: { userId } }));
}


export function RecentStockTracker({
  companyName,
  currency,
  symbol,
  userId,
}: {
  companyName: string;
  currency: string;
  symbol: string;
  userId: string;
}) {
  useEffect(() => {
    try {
      const current = readRecentStocks(userId).filter((item) => item.symbol !== symbol);
      saveRecentStocks(userId, [
        { companyName, currency, symbol, viewedAt: new Date().toISOString() },
        ...current,
      ]);
    } catch {
      // The feature remains optional when browser storage is unavailable.
    }
  }, [companyName, currency, symbol, userId]);

  return null;
}


export function RecentStocks({ userId }: { userId: string }) {
  const [items, setItems] = useState<RecentStock[] | null>(null);

  const refresh = useCallback(() => {
    setItems(readRecentStocks(userId).slice(0, MAX_VISIBLE_ITEMS));
  }, [userId]);

  useEffect(() => {
    refresh();
    const handleStorage = (event: StorageEvent) => {
      if (event.key === storageKey(userId)) refresh();
    };
    const handleUpdate = (event: Event) => {
      const detail = (event as CustomEvent<{ userId?: string }>).detail;
      if (detail?.userId === userId) refresh();
    };
    window.addEventListener("storage", handleStorage);
    window.addEventListener(UPDATE_EVENT, handleUpdate);
    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener(UPDATE_EVENT, handleUpdate);
    };
  }, [refresh, userId]);

  const clearHistory = () => {
    try {
      window.localStorage.removeItem(storageKey(userId));
    } catch {
      // Keep the UI usable when browser storage is unavailable.
    }
    setItems([]);
  };

  return (
    <section>
      <div className="rowBetween gap sectionTitleRow">
        <h2>최근 관심 종목</h2>
        {items && items.length > 0 && (
          <button className="secondaryButton" onClick={clearHistory} type="button">
            기록 삭제
          </button>
        )}
      </div>
      <p className="searchNotice">최근 확인한 종목을 이 기기에서 다시 볼 수 있습니다.</p>
      {items === null ? null : items.length === 0 ? (
        <div className="card emptyState">종목 상세 화면을 확인하면 최근 관심 종목에 표시됩니다.</div>
      ) : (
        <div className="recentStockGrid">
          {items.map((item) => (
            <Link className="card recentStockCard" href={`/stocks/${item.symbol}`} key={item.symbol}>
              <div>
                <div className="eyebrow">{item.symbol}</div>
                <h3>{item.companyName}</h3>
              </div>
              <div className="meta">
                {item.currency} · {new Date(item.viewedAt).toLocaleString("ko-KR")}
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
