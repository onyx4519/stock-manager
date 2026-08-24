import type { DataStatus, StockQuote } from "@/types/market";

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

async function request<T>(url: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { cache: "no-store" });
  } catch {
    throw new ApiError("백엔드 서버에 연결할 수 없습니다.");
  }

  if (!response.ok) {
    throw new ApiError("백엔드가 요청을 처리하지 못했습니다.", response.status);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError("백엔드 응답 형식이 올바르지 않습니다.");
  }
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
