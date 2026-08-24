import type { StockQuote } from "@/types/market";
import { DataBadge } from "./DataBadge";

const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", { style: "currency", currency, maximumFractionDigits: currency === "KRW" ? 0 : 2 }).format(value);

export function QuoteCard({ quote }: { quote: StockQuote }) {
  return (
    <article className="card">
      <div className="rowBetween gap">
        <div>
          <div className="eyebrow">{quote.symbol}</div>
          <h3>{quote.companyName}</h3>
        </div>
        <DataBadge status={quote.dataStatus} />
      </div>
      <div className="price">{money(quote.price, quote.currency)}</div>
      <div className="muted">등락 {quote.changePercent > 0 ? "+" : ""}{quote.changePercent.toFixed(2)}%</div>
      <div className="meta">기준 {new Date(quote.timestamp).toLocaleString("ko-KR")} · {quote.provider}</div>
    </article>
  );
}
