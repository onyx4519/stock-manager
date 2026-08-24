import type { PortfolioPosition } from "@/types/market";

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
