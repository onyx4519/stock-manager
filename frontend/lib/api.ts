import "server-only";

import type {
  CurrencySummary,
  DataStatus,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioTransaction,
  StockQuote,
  TransactionInput,
  TransactionType,
  WatchlistItem,
} from "@/types/market";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

type BackendStockQuote = {
  symbol: string;
  company_name: string;
  price: number;
  change_percent: number;
  currency: string;
  timestamp: string;
  data_status: DataStatus;
  provider: string;
};

type BackendPosition = {
  symbol: string;
  company_name: string;
  quantity: number | string;
  average_cost: number | string;
  current_price: number | string;
  currency: string;
  cost_basis: number | string;
  market_value: number | string;
  realized_pnl: number | string;
  unrealized_pnl: number | string;
  return_percent: number | string;
  weight_percent: number | string;
  data_status: DataStatus;
  provider: string;
  quoted_at: string;
};

type BackendTransaction = {
  id: number;
  symbol: string;
  transaction_type: TransactionType;
  quantity: number | string;
  price: number | string;
  currency: string;
  fee: number | string;
  tax: number | string;
  executed_at: string;
  created_at: string;
  updated_at: string;
};

type BackendCurrencySummary = {
  currency: string;
  cost_basis: number | string;
  market_value: number | string;
  realized_pnl: number | string;
  unrealized_pnl: number | string;
};

type BackendPortfolioSummary = {
  positions_count: number;
  currencies: BackendCurrencySummary[];
};

type BackendWatchlistItem = {
  symbol: string;
  company_name: string;
  currency: string;
  created_at: string;
  price: number | null;
  change_percent: number | null;
  timestamp: string | null;
  data_status: DataStatus;
  provider: string | null;
};

export type BackendHealth = {
  status: string;
  mock_mode: boolean;
  market_provider: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      cache: "no-store",
      headers: {
        ...(init.body ? { "content-type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError("백엔드 서버에 연결할 수 없습니다.");
  }

  if (!response.ok) {
    let message = "백엔드가 요청을 처리하지 못했습니다.";
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === "string") message = payload.detail;
    } catch {
      // Keep the sanitized fallback when the error body is not JSON.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("백엔드 응답 형식이 올바르지 않습니다.");
  }
}

function normalizePosition(position: BackendPosition): PortfolioPosition {
  return {
    symbol: position.symbol,
    companyName: position.company_name,
    quantity: Number(position.quantity),
    averageCost: Number(position.average_cost),
    currentPrice: Number(position.current_price),
    currency: position.currency,
    costBasis: Number(position.cost_basis),
    marketValue: Number(position.market_value),
    realizedPnl: Number(position.realized_pnl),
    unrealizedPnl: Number(position.unrealized_pnl),
    returnPercent: Number(position.return_percent),
    weightPercent: Number(position.weight_percent),
    dataStatus: position.data_status,
    provider: position.provider,
    quotedAt: position.quoted_at,
  };
}

function normalizeTransaction(transaction: BackendTransaction): PortfolioTransaction {
  return {
    id: transaction.id,
    symbol: transaction.symbol,
    transactionType: transaction.transaction_type,
    quantity: Number(transaction.quantity),
    price: Number(transaction.price),
    currency: transaction.currency,
    fee: Number(transaction.fee),
    tax: Number(transaction.tax),
    executedAt: transaction.executed_at,
    createdAt: transaction.created_at,
    updatedAt: transaction.updated_at,
  };
}

function normalizeCurrencySummary(summary: BackendCurrencySummary): CurrencySummary {
  return {
    currency: summary.currency,
    costBasis: Number(summary.cost_basis),
    marketValue: Number(summary.market_value),
    realizedPnl: Number(summary.realized_pnl),
    unrealizedPnl: Number(summary.unrealized_pnl),
  };
}

function normalizeQuote(quote: BackendStockQuote): StockQuote {
  return {
    symbol: quote.symbol,
    companyName: quote.company_name,
    price: quote.price,
    changePercent: quote.change_percent,
    currency: quote.currency,
    timestamp: quote.timestamp,
    dataStatus: quote.data_status,
    provider: quote.provider,
  };
}

function normalizeWatchlistItem(item: BackendWatchlistItem): WatchlistItem {
  return {
    symbol: item.symbol,
    companyName: item.company_name,
    currency: item.currency,
    createdAt: item.created_at,
    price: item.price,
    changePercent: item.change_percent,
    timestamp: item.timestamp,
    dataStatus: item.data_status,
    provider: item.provider,
  };
}

export async function getHealth(): Promise<BackendHealth> {
  const backendOrigin = new URL(API_BASE_URL).origin;
  return request<BackendHealth>(`${backendOrigin}/health`);
}

export async function getQuotes(): Promise<StockQuote[]> {
  const quotes = await request<BackendStockQuote[]>(`${API_BASE_URL}/market/quotes`);
  return quotes.map(normalizeQuote);
}

export async function getQuote(symbol: string): Promise<StockQuote> {
  const quote = await request<BackendStockQuote>(
    `${API_BASE_URL}/market/quotes/${encodeURIComponent(symbol)}`,
  );
  return normalizeQuote(quote);
}

export async function searchStocks(query = ""): Promise<StockQuote[]> {
  const url = new URL(`${API_BASE_URL}/stocks`);
  if (query.trim()) url.searchParams.set("q", query.trim());
  const quotes = await request<BackendStockQuote[]>(url.toString());
  return quotes.map(normalizeQuote);
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const items = await request<BackendWatchlistItem[]>(`${API_BASE_URL}/watchlist`);
  return items.map(normalizeWatchlistItem);
}

export async function addWatchlistItem(symbol: string): Promise<WatchlistItem> {
  const item = await request<BackendWatchlistItem>(`${API_BASE_URL}/watchlist`, {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
  return normalizeWatchlistItem(item);
}

export async function deleteWatchlistItem(symbol: string): Promise<void> {
  return request<void>(`${API_BASE_URL}/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}

export async function getPortfolioPositions(): Promise<PortfolioPosition[]> {
  const positions = await request<BackendPosition[]>(`${API_BASE_URL}/portfolio/positions`);
  return positions.map(normalizePosition);
}

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  const summary = await request<BackendPortfolioSummary>(`${API_BASE_URL}/portfolio/summary`);
  return {
    positionsCount: summary.positions_count,
    currencies: summary.currencies.map(normalizeCurrencySummary),
  };
}

export async function getTransactions(): Promise<PortfolioTransaction[]> {
  const transactions = await request<BackendTransaction[]>(`${API_BASE_URL}/transactions`);
  return transactions.map(normalizeTransaction);
}

export async function createTransaction(input: TransactionInput): Promise<PortfolioTransaction> {
  const transaction = await request<BackendTransaction>(`${API_BASE_URL}/transactions`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return normalizeTransaction(transaction);
}

export async function updateTransaction(
  transactionId: number,
  input: TransactionInput,
): Promise<PortfolioTransaction> {
  const transaction = await request<BackendTransaction>(
    `${API_BASE_URL}/transactions/${transactionId}`,
    { method: "PATCH", body: JSON.stringify(input) },
  );
  return normalizeTransaction(transaction);
}

export async function deleteTransaction(transactionId: number): Promise<void> {
  return request<void>(`${API_BASE_URL}/transactions/${transactionId}`, {
    method: "DELETE",
  });
}
