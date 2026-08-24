import type { StockQuote } from "@/types/market";
import { DataBadge } from "./DataBadge";

const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", { style: "currency", currency, maximumFractionDigits: currency === "KRW" ? 0 : 2 }).format(value);

export function QuoteCard({
  colorizeChange = false,
  quote,
}: {
  colorizeChange?: boolean;
  quote: StockQuote;
}) {
  const direction = quote.changePercent > 0 ? "up" : quote.changePercent < 0 ? "down" : "flat";
  const changeClass = colorizeChange ? `quoteChange-${direction}` : "muted";
  const directionMark = direction === "up" ? "▲" : direction === "down" ? "▼" : "—";

  return (
    <article className="card">
      <div className="rowBetween gap">
        <div>
          <div className="eyebrow">{quote.symbol}</div>
          <h3>{quote.companyName}</h3>
        </div>
        <DataBadge status={quote.dataStatus} />
      </div>
      <div className={`price ${changeClass}`}>{money(quote.price, quote.currency)}</div>
      <div className={`quoteChange ${changeClass}`}>
        등락 {directionMark} {quote.changePercent > 0 ? "+" : ""}{quote.changePercent.toFixed(2)}%
      </div>
      <div className="meta">기준 {new Date(quote.timestamp).toLocaleString("ko-KR")} · {quote.provider}</div>
    </article>
  );
}
