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

export type WatchlistItem = {
  symbol: string;
  companyName: string;
  currency: string;
  createdAt: string;
  price: number | null;
  changePercent: number | null;
  timestamp: string | null;
  dataStatus: DataStatus;
  provider: string | null;
};

export type DartCompany = {
  corporationCode: string;
  corporationName: string;
  corporationEnglishName: string | null;
  stockCode: string | null;
  modifyDate: string | null;
};

export type DartDisclosure = {
  corporationClass: string;
  corporationName: string;
  corporationCode: string;
  stockCode: string | null;
  reportName: string;
  receiptNumber: string;
  filerName: string;
  receiptDate: string;
  remarks: string | null;
  viewerUrl: string;
};

export type DartDisclosureList = {
  company: DartCompany;
  totalCount: number;
  items: DartDisclosure[];
};

export type DartFinancialAccount = {
  receiptNumber: string;
  businessYear: string;
  reportCode: string;
  accountName: string;
  financialStatementDivision: string;
  financialStatementName: string;
  statementDivision: string;
  statementName: string;
  currentTermName: string | null;
  currentTermDate: string | null;
  currentTermAmount: number | null;
  currentTermCumulativeAmount: number | null;
  previousTermName: string | null;
  previousTermDate: string | null;
  previousTermAmount: number | null;
  currency: string | null;
};

export type DartFinancialStatement = {
  company: DartCompany;
  businessYear: string;
  reportCode: string;
  financialStatementDivision: string | null;
  accounts: DartFinancialAccount[];
};

export type NewsArticle = {
  id: string;
  title: string;
  author: string | null;
  description: string | null;
  articleUrl: string;
  imageUrl: string | null;
  publisherName: string;
  publisherHomepageUrl: string | null;
  publishedAt: string;
  tickers: string[];
  provider: string;
};

export type NewsFeed = {
  symbols: string[];
  items: NewsArticle[];
  totalCount: number;
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
