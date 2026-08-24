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
  costBasis: number;
  marketValue: number;
  realizedPnl: number;
  unrealizedPnl: number;
  returnPercent: number;
  weightPercent: number;
  dataStatus: DataStatus;
  provider: string;
  quotedAt: string;
};

export type TransactionType = "BUY" | "SELL";

export type PortfolioTransaction = {
  id: number;
  symbol: string;
  transactionType: TransactionType;
  quantity: number;
  price: number;
  currency: string;
  fee: number;
  tax: number;
  executedAt: string;
  createdAt: string;
  updatedAt: string;
};

export type CurrencySummary = {
  currency: string;
  costBasis: number;
  marketValue: number;
  realizedPnl: number;
  unrealizedPnl: number;
};

export type PortfolioSummary = {
  positionsCount: number;
  currencies: CurrencySummary[];
};

export type TransactionInput = {
  symbol: string;
  transaction_type: TransactionType;
  quantity: string;
  price: string;
  currency: string;
  fee: string;
  tax: string;
  executed_at: string;
};
