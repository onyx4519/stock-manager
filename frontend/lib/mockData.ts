import type { PortfolioPosition, StockQuote } from "@/types/market";

export const mockQuotes: StockQuote[] = [
  {
    symbol: "NVDA",
    companyName: "NVIDIA Corporation",
    price: 120.5,
    changePercent: 1.8,
    currency: "USD",
    timestamp: "2026-08-24T16:20:00+09:00",
    dataStatus: "MOCK",
    provider: "MockProvider",
  },
  {
    symbol: "005930",
    companyName: "삼성전자",
    price: 78000,
    changePercent: -0.6,
    currency: "KRW",
    timestamp: "2026-08-24T16:20:00+09:00",
    dataStatus: "MOCK",
    provider: "MockProvider",
  },
];

export const mockPortfolio: PortfolioPosition[] = [
  {
    symbol: "NVDA",
    companyName: "NVIDIA Corporation",
    quantity: 5,
    averageCost: 108,
    currentPrice: 120.5,
    currency: "USD",
    marketValue: 602.5,
    unrealizedPnl: 62.5,
    weightPercent: 42.4,
  },
  {
    symbol: "005930",
    companyName: "삼성전자",
    quantity: 10,
    averageCost: 75000,
    currentPrice: 78000,
    currency: "KRW",
    marketValue: 780000,
    unrealizedPnl: 30000,
    weightPercent: 57.6,
  },
];
