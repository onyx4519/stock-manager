"use client";

import { FormEvent, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import {
  deleteTransactionAction,
  saveTransactionAction,
} from "@/app/portfolio/actions";
import { DataBadge } from "@/components/DataBadge";
import type {
  PortfolioPosition,
  PortfolioSummary,
  PortfolioTransaction,
  StockQuote,
  TransactionInput,
  TransactionType,
} from "@/types/market";


type FormState = {
  transactionId: number | null;
  symbol: string;
  transactionType: TransactionType;
  quantity: string;
  price: string;
  currency: string;
  fee: string;
  tax: string;
  executedAt: string;
};


const money = (value: number, currency: string) =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(value);


function localDateTime(value = new Date()): string {
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}


function emptyForm(quotes: StockQuote[]): FormState {
  const quote = quotes[0];
  return {
    transactionId: null,
    symbol: quote?.symbol ?? "",
    transactionType: "BUY",
    quantity: "",
    price: quote ? String(quote.price) : "",
    currency: quote?.currency ?? "",
    fee: "0",
    tax: "0",
    executedAt: localDateTime(),
  };
}


export function PortfolioManager({
  positions,
  summary,
  transactions,
  quotes,
}: {
  positions: PortfolioPosition[];
  summary: PortfolioSummary;
  transactions: PortfolioTransaction[];
  quotes: StockQuote[];
}) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [form, setForm] = useState<FormState>(() => emptyForm(quotes));
  const [message, setMessage] = useState<string | null>(null);

  const openCreateForm = () => {
    setForm(emptyForm(quotes));
    setMessage(null);
    setIsFormOpen(true);
  };

  const openEditForm = (transaction: PortfolioTransaction) => {
    setForm({
      transactionId: transaction.id,
      symbol: transaction.symbol,
      transactionType: transaction.transactionType,
      quantity: String(transaction.quantity),
      price: String(transaction.price),
      currency: transaction.currency,
      fee: String(transaction.fee),
      tax: String(transaction.tax),
      executedAt: localDateTime(new Date(transaction.executedAt)),
    });
    setMessage(null);
    setIsFormOpen(true);
  };

  const selectSymbol = (symbol: string) => {
    const quote = quotes.find((item) => item.symbol === symbol);
    setForm((current) => ({
      ...current,
      symbol,
      currency: quote?.currency ?? "",
      price: quote ? String(quote.price) : current.price,
    }));
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage(null);
    const input: TransactionInput = {
      symbol: form.symbol,
      transaction_type: form.transactionType,
      quantity: form.quantity,
      price: form.price,
      currency: form.currency,
      fee: form.fee || "0",
      tax: form.tax || "0",
      executed_at: new Date(form.executedAt).toISOString(),
    };

    startTransition(async () => {
      const result = await saveTransactionAction(form.transactionId, input);
      if (!result.ok) {
        setMessage(result.message ?? "거래를 저장하지 못했습니다.");
        return;
      }
      setIsFormOpen(false);
      setForm(emptyForm(quotes));
      router.refresh();
    });
  };

  const handleDelete = (transactionId: number) => {
    if (!window.confirm("이 거래를 삭제하시겠습니까?")) return;
    setMessage(null);
    startTransition(async () => {
      const result = await deleteTransactionAction(transactionId);
      if (!result.ok) {
        setMessage(result.message ?? "거래를 삭제하지 못했습니다.");
        return;
      }
      router.refresh();
    });
  };

  return (
    <div className="page">
      <div className="pageHeader">
        <div>
          <div className="eyebrow">Portfolio</div>
          <h1>내 포트폴리오</h1>
          <p className="muted">거래 원장과 실제 EOD 시세를 기준으로 계산합니다.</p>
        </div>
        <button className="primaryButton" onClick={openCreateForm} type="button">
          + 거래 추가
        </button>
      </div>

      {message && <div className="card formMessage" role="alert">{message}</div>}

      {isFormOpen && (
        <form className="card transactionForm" onSubmit={handleSubmit}>
          <div className="rowBetween gap">
            <div>
              <div className="eyebrow">Transaction</div>
              <h2>{form.transactionId === null ? "거래 추가" : "거래 수정"}</h2>
            </div>
            <button
              className="secondaryButton"
              onClick={() => setIsFormOpen(false)}
              type="button"
            >
              닫기
            </button>
          </div>
          <div className="formGrid">
            <label>
              종목
              <select
                disabled={form.transactionId !== null}
                onChange={(event) => selectSymbol(event.target.value)}
                required
                value={form.symbol}
              >
                {quotes.map((quote) => (
                  <option key={quote.symbol} value={quote.symbol}>
                    {quote.symbol} · {quote.companyName}
                  </option>
                ))}
              </select>
            </label>
            <label>
              구분
              <select
                onChange={(event) => setForm((current) => ({
                  ...current,
                  transactionType: event.target.value as TransactionType,
                }))}
                value={form.transactionType}
              >
                <option value="BUY">매수</option>
                <option value="SELL">매도</option>
              </select>
            </label>
            <label>
              수량
              <input
                min="0.0000000001"
                onChange={(event) => setForm((current) => ({ ...current, quantity: event.target.value }))}
                required
                step="any"
                type="number"
                value={form.quantity}
              />
            </label>
            <label>
              거래단가 ({form.currency})
              <input
                min="0.0000000001"
                onChange={(event) => setForm((current) => ({ ...current, price: event.target.value }))}
                required
                step="any"
                type="number"
                value={form.price}
              />
            </label>
            <label>
              수수료
              <input
                min="0"
                onChange={(event) => setForm((current) => ({ ...current, fee: event.target.value }))}
                step="any"
                type="number"
                value={form.fee}
              />
            </label>
            <label>
              세금
              <input
                min="0"
                onChange={(event) => setForm((current) => ({ ...current, tax: event.target.value }))}
                step="any"
                type="number"
                value={form.tax}
              />
            </label>
            <label>
              거래일시
              <input
                onChange={(event) => setForm((current) => ({ ...current, executedAt: event.target.value }))}
                required
                type="datetime-local"
                value={form.executedAt}
              />
            </label>
          </div>
          <div className="formActions">
            <button className="primaryButton" disabled={isPending || quotes.length === 0} type="submit">
              {isPending ? "저장 중" : "거래 저장"}
            </button>
          </div>
        </form>
      )}

      <section>
        <h2>통화별 요약</h2>
        {summary.currencies.length === 0 ? (
          <div className="card emptyState">등록된 거래가 없습니다.</div>
        ) : (
          <div className="grid2">
            {summary.currencies.map((item) => (
              <article className="card" key={item.currency}>
                <div className="eyebrow">{item.currency}</div>
                <h3>평가금액 {money(item.marketValue, item.currency)}</h3>
                <div className="summaryMetrics">
                  <span>매입금액 <b>{money(item.costBasis, item.currency)}</b></span>
                  <span>미실현손익 <b>{money(item.unrealizedPnl, item.currency)}</b></span>
                  <span>실현손익 <b>{money(item.realizedPnl, item.currency)}</b></span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2>보유 종목</h2>
        {positions.length === 0 ? (
          <div className="card emptyState">매수 거래를 등록하면 보유 종목이 표시됩니다.</div>
        ) : (
          <div className="portfolioList">
            {positions.map((position) => (
              <article className="card positionCard" key={position.symbol}>
                <div>
                  <strong>{position.companyName}</strong>
                  <div className="muted">{position.symbol} · {position.provider}</div>
                  <DataBadge status={position.dataStatus} />
                </div>
                <div className="positionMetrics">
                  <span>수량 <b>{position.quantity.toLocaleString("ko-KR")}</b></span>
                  <span>평균단가 <b>{money(position.averageCost, position.currency)}</b></span>
                  <span>현재가 <b>{money(position.currentPrice, position.currency)}</b></span>
                  <span>평가금액 <b>{money(position.marketValue, position.currency)}</b></span>
                  <span>미실현손익 <b>{money(position.unrealizedPnl, position.currency)}</b></span>
                  <span>수익률 <b>{position.returnPercent.toFixed(2)}%</b></span>
                  <span>통화 내 비중 <b>{position.weightPercent.toFixed(1)}%</b></span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2>거래 내역</h2>
        {transactions.length === 0 ? (
          <div className="card emptyState">아직 거래 내역이 없습니다.</div>
        ) : (
          <div className="transactionList">
            {transactions.map((transaction) => (
              <article className="card transactionRow" key={transaction.id}>
                <div>
                  <div className={`transactionType transactionType-${transaction.transactionType.toLowerCase()}`}>
                    {transaction.transactionType === "BUY" ? "매수" : "매도"}
                  </div>
                  <strong>{transaction.symbol}</strong>
                  <div className="meta">{new Date(transaction.executedAt).toLocaleString("ko-KR")}</div>
                </div>
                <div className="transactionNumbers">
                  <span>{transaction.quantity.toLocaleString("ko-KR")}주</span>
                  <b>{money(transaction.price, transaction.currency)}</b>
                  <span>비용 {money(transaction.fee + transaction.tax, transaction.currency)}</span>
                </div>
                <div className="rowActions">
                  <button className="secondaryButton" onClick={() => openEditForm(transaction)} type="button">수정</button>
                  <button className="dangerButton" disabled={isPending} onClick={() => handleDelete(transaction.id)} type="button">삭제</button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
