export type DataStatus = "REALTIME" | "DELAYED" | "EOD" | "MOCK" | "UNAVAILABLE";
export type Gender = "UNSPECIFIED" | "MALE" | "FEMALE";
export type UserRole = "USER" | "ADMIN";
export type NotificationCategory = "NOTICE" | "ACCOUNT" | "SERVICE";

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

export type StockSearchItem = {
  symbol: string;
  companyName: string;
  market: string;
  currency: string;
  provider: string;
  price: number | null;
  changePercent: number | null;
  timestamp: string | null;
  dataStatus: DataStatus;
};

export type StockSearchResponse = {
  query: string | null;
  totalCount: number;
  items: StockSearchItem[];
  sources: string[];
  warnings: string[];
};

export type AuthUser = {
  id: string;
  email: string;
  displayName: string;
  birthDate: string | null;
  gender: Gender;
  role: UserRole;
  passwordChangeRequired: boolean;
  personalizationConsent: boolean;
  personalizationConsentAt: string | null;
  serviceNotificationConsent: boolean;
  serviceNotificationConsentAt: string | null;
  createdAt: string;
};

export type NotificationItem = {
  id: number;
  category: NotificationCategory;
  title: string;
  message: string;
  createdAt: string;
  readAt: string | null;
};

export type NotificationList = {
  items: NotificationItem[];
  unreadCount: number;
};

export type AuthSession = {
  accessToken: string;
  tokenType: string;
  expiresAt: string;
  user: AuthUser;
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

export type MetricAssessment =
  | "HEALTHY"
  | "WATCH"
  | "CAUTION"
  | "NOT_EVALUATED"
  | "UNAVAILABLE";

export type FinancialRiskLevel = "LOW" | "MODERATE" | "HIGH" | "UNAVAILABLE";

export type FinancialMetric = {
  code: string;
  name: string;
  category: string;
  value: number | null;
  unit: string;
  source: string;
  isRiskIndicator: boolean;
  assessment: MetricAssessment;
  interpretation: string;
};

export type FinancialHealthAnalysis = {
  company: DartCompany;
  businessYear: string;
  reportCode: string;
  settlementDate: string | null;
  metrics: FinancialMetric[];
  financialRiskScore: number | null;
  financialRiskLevel: FinancialRiskLevel;
  evaluatedIndicators: number;
  methodology: string;
  warnings: string[];
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
