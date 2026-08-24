export type DataStatus = "REALTIME" | "DELAYED" | "EOD" | "MOCK" | "UNAVAILABLE";

export type StockQuote = {
  symbol: string;
  companyName: string;
  price: number;
  changePercent: number;
  currency: string;
  timestamp: string;
  dataStatus: DataStatus;
  provider: string;
};

export type PortfolioPosition = {
  symbol: string;
  companyName: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  currency: string;
  marketValue: number;
  unrealizedPnl: number;
  weightPercent: number;
};
