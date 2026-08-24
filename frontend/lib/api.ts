import "server-only";

import { cookies } from "next/headers";

import type {
  CurrencySummary,
  AuthSession,
  AuthUser,
  DartCompany,
  DartDisclosure,
  DartDisclosureList,
  DartFinancialAccount,
  DartFinancialStatement,
  DataStatus,
  FinancialHealthAnalysis,
  FinancialMetric,
  FinancialRiskLevel,
  Gender,
  MetricAssessment,
  NewsArticle,
  NewsFeed,
  NotificationCategory,
  NotificationList,
  PortfolioPosition,
  PortfolioSummary,
  PortfolioTransaction,
  StockQuote,
  StockSearchResponse,
  TransactionInput,
  TransactionType,
  WatchlistItem,
  UserRole,
} from "@/types/market";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const SESSION_COOKIE_NAME = "stock_manager_session";

type BackendAuthUser = {
  id: string;
  email: string;
  display_name: string;
  birth_date: string | null;
  gender: Gender;
  role: UserRole;
  personalization_consent: boolean;
  personalization_consent_at: string | null;
  service_notification_consent: boolean;
  service_notification_consent_at: string | null;
  created_at: string;
};

type BackendNotificationItem = {
  id: number;
  category: NotificationCategory;
  title: string;
  message: string;
  created_at: string;
  read_at: string | null;
};

type BackendNotificationList = {
  items: BackendNotificationItem[];
  unread_count: number;
};

type BackendAuthSession = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: BackendAuthUser;
};

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

type BackendStockSearchItem = {
  symbol: string;
  company_name: string;
  market: string;
  currency: string;
  provider: string;
  price: number | null;
  change_percent: number | null;
  timestamp: string | null;
  data_status: DataStatus;
};

type BackendStockSearchResponse = {
  query: string | null;
  total_count: number;
  items: BackendStockSearchItem[];
  sources: string[];
  warnings: string[];
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

type BackendDartCompany = {
  corp_code: string;
  corp_name: string;
  corp_eng_name: string | null;
  stock_code: string | null;
  modify_date: string | null;
};

type BackendDartDisclosure = {
  corporation_class: string;
  corporation_name: string;
  corporation_code: string;
  stock_code: string | null;
  report_name: string;
  receipt_number: string;
  filer_name: string;
  receipt_date: string;
  remarks: string | null;
  viewer_url: string;
};

type BackendDartDisclosureList = {
  company: BackendDartCompany;
  total_count: number;
  items: BackendDartDisclosure[];
};

type BackendDartFinancialAccount = {
  receipt_number: string;
  business_year: string;
  report_code: string;
  account_name: string;
  financial_statement_division: string;
  financial_statement_name: string;
  statement_division: string;
  statement_name: string;
  current_term_name: string | null;
  current_term_date: string | null;
  current_term_amount: number | null;
  current_term_cumulative_amount: number | null;
  previous_term_name: string | null;
  previous_term_date: string | null;
  previous_term_amount: number | null;
  currency: string | null;
};

type BackendDartFinancialStatement = {
  company: BackendDartCompany;
  business_year: string;
  report_code: string;
  financial_statement_division: string | null;
  accounts: BackendDartFinancialAccount[];
};

type BackendNewsArticle = {
  id: string;
  title: string;
  author: string | null;
  description: string | null;
  article_url: string;
  image_url: string | null;
  publisher_name: string;
  publisher_homepage_url: string | null;
  published_at: string;
  tickers: string[];
  provider: string;
};

type BackendNewsFeed = {
  symbols: string[];
  items: BackendNewsArticle[];
  total_count: number;
};

type BackendFinancialMetric = {
  code: string;
  name: string;
  category: string;
  value: number | null;
  unit: string;
  source: string;
  is_risk_indicator: boolean;
  assessment: MetricAssessment;
  interpretation: string;
};

type BackendFinancialHealthAnalysis = {
  company: BackendDartCompany;
  business_year: string;
  report_code: string;
  settlement_date: string | null;
  metrics: BackendFinancialMetric[];
  financial_risk_score: number | null;
  financial_risk_level: FinancialRiskLevel;
  evaluated_indicators: number;
  methodology: string;
  warnings: string[];
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
    const token = (await cookies()).get(SESSION_COOKIE_NAME)?.value;
    response = await fetch(url, {
      ...init,
      cache: "no-store",
      headers: {
        ...(init.body ? { "content-type": "application/json" } : {}),
        ...(token ? { authorization: `Bearer ${token}` } : {}),
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

function normalizeAuthUser(user: BackendAuthUser): AuthUser {
  return {
    id: user.id,
    email: user.email,
    displayName: user.display_name,
    birthDate: user.birth_date,
    gender: user.gender,
    role: user.role,
    personalizationConsent: user.personalization_consent,
    personalizationConsentAt: user.personalization_consent_at,
    serviceNotificationConsent: user.service_notification_consent,
    serviceNotificationConsentAt: user.service_notification_consent_at,
    createdAt: user.created_at,
  };
}

function normalizeAuthSession(session: BackendAuthSession): AuthSession {
  return {
    accessToken: session.access_token,
    tokenType: session.token_type,
    expiresAt: session.expires_at,
    user: normalizeAuthUser(session.user),
  };
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

function normalizeDartCompany(company: BackendDartCompany): DartCompany {
  return {
    corporationCode: company.corp_code,
    corporationName: company.corp_name,
    corporationEnglishName: company.corp_eng_name,
    stockCode: company.stock_code,
    modifyDate: company.modify_date,
  };
}

function normalizeDartDisclosure(item: BackendDartDisclosure): DartDisclosure {
  return {
    corporationClass: item.corporation_class,
    corporationName: item.corporation_name,
    corporationCode: item.corporation_code,
    stockCode: item.stock_code,
    reportName: item.report_name,
    receiptNumber: item.receipt_number,
    filerName: item.filer_name,
    receiptDate: item.receipt_date,
    remarks: item.remarks,
    viewerUrl: item.viewer_url,
  };
}

function normalizeDartFinancialAccount(
  item: BackendDartFinancialAccount,
): DartFinancialAccount {
  return {
    receiptNumber: item.receipt_number,
    businessYear: item.business_year,
    reportCode: item.report_code,
    accountName: item.account_name,
    financialStatementDivision: item.financial_statement_division,
    financialStatementName: item.financial_statement_name,
    statementDivision: item.statement_division,
    statementName: item.statement_name,
    currentTermName: item.current_term_name,
    currentTermDate: item.current_term_date,
    currentTermAmount: item.current_term_amount,
    currentTermCumulativeAmount: item.current_term_cumulative_amount,
    previousTermName: item.previous_term_name,
    previousTermDate: item.previous_term_date,
    previousTermAmount: item.previous_term_amount,
    currency: item.currency,
  };
}

function normalizeNewsArticle(item: BackendNewsArticle): NewsArticle {
  return {
    id: item.id,
    title: item.title,
    author: item.author,
    description: item.description,
    articleUrl: item.article_url,
    imageUrl: item.image_url,
    publisherName: item.publisher_name,
    publisherHomepageUrl: item.publisher_homepage_url,
    publishedAt: item.published_at,
    tickers: item.tickers,
    provider: item.provider,
  };
}

function normalizeFinancialMetric(item: BackendFinancialMetric): FinancialMetric {
  return {
    code: item.code,
    name: item.name,
    category: item.category,
    value: item.value,
    unit: item.unit,
    source: item.source,
    isRiskIndicator: item.is_risk_indicator,
    assessment: item.assessment,
    interpretation: item.interpretation,
  };
}

export async function getHealth(): Promise<BackendHealth> {
  const backendOrigin = new URL(API_BASE_URL).origin;
  return request<BackendHealth>(`${backendOrigin}/health`);
}

export async function registerUser(input: {
  email: string;
  display_name: string;
  password: string;
  birth_date: string;
  gender: Gender;
  account_creation_consent: true;
  privacy_collection_consent: true;
  personalization_consent: boolean;
  service_notification_consent: boolean;
}): Promise<AuthSession> {
  const session = await request<BackendAuthSession>(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return normalizeAuthSession(session);
}

export async function loginUser(input: {
  email: string;
  password: string;
}): Promise<AuthSession> {
  const session = await request<BackendAuthSession>(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return normalizeAuthSession(session);
}

export async function getCurrentUser(): Promise<AuthUser | null> {
  try {
    const user = await request<BackendAuthUser>(`${API_BASE_URL}/auth/me`);
    return normalizeAuthUser(user);
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export async function logoutUser(): Promise<void> {
  return request<void>(`${API_BASE_URL}/auth/logout`, { method: "POST" });
}

export async function deleteAccount(input: {
  confirmed: true;
  reason:
    | "MISSING_CONTENT"
    | "DIFFICULT_TO_USE"
    | "DATA_QUALITY"
    | "PRIVACY_CONCERN"
    | "NO_LONGER_NEEDED"
    | "NO_REASON";
}): Promise<void> {
  return request<void>(`${API_BASE_URL}/auth/account`, {
    method: "DELETE",
    body: JSON.stringify(input),
  });
}

export async function updateNotificationPreference(
  enabled: boolean,
): Promise<AuthUser> {
  const user = await request<BackendAuthUser>(
    `${API_BASE_URL}/auth/preferences/notifications`,
    {
      method: "PATCH",
      body: JSON.stringify({ service_notification_consent: enabled }),
    },
  );
  return normalizeAuthUser(user);
}

export async function changePassword(input: {
  currentPassword: string;
  newPassword: string;
}): Promise<void> {
  return request<void>(`${API_BASE_URL}/auth/password`, {
    method: "PATCH",
    body: JSON.stringify({
      current_password: input.currentPassword,
      new_password: input.newPassword,
    }),
  });
}

export async function getNotifications(): Promise<NotificationList> {
  const result = await request<BackendNotificationList>(`${API_BASE_URL}/notifications`);
  return {
    items: result.items.map((item) => ({
      id: item.id,
      category: item.category,
      title: item.title,
      message: item.message,
      createdAt: item.created_at,
      readAt: item.read_at,
    })),
    unreadCount: result.unread_count,
  };
}

export async function markNotificationRead(notificationId: number): Promise<void> {
  return request<void>(`${API_BASE_URL}/notifications/${notificationId}/read`, {
    method: "PATCH",
  });
}

export async function markAllNotificationsRead(): Promise<void> {
  return request<void>(`${API_BASE_URL}/notifications/read-all`, {
    method: "PATCH",
  });
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

export async function searchStocks(query = ""): Promise<StockSearchResponse> {
  const url = new URL(`${API_BASE_URL}/stocks`);
  if (query.trim()) url.searchParams.set("q", query.trim());
  const result = await request<BackendStockSearchResponse>(url.toString());
  return {
    query: result.query,
    totalCount: result.total_count,
    items: result.items.map((item) => ({
      symbol: item.symbol,
      companyName: item.company_name,
      market: item.market,
      currency: item.currency,
      provider: item.provider,
      price: item.price,
      changePercent: item.change_percent,
      timestamp: item.timestamp,
      dataStatus: item.data_status,
    })),
    sources: result.sources,
    warnings: result.warnings,
  };
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

export async function getDartDisclosures(
  stockCode: string,
  days = 365,
  limit = 20,
): Promise<DartDisclosureList> {
  const url = new URL(
    `${API_BASE_URL}/dart/companies/${encodeURIComponent(stockCode)}/disclosures`,
  );
  url.searchParams.set("days", String(days));
  url.searchParams.set("limit", String(limit));
  const result = await request<BackendDartDisclosureList>(url.toString());
  return {
    company: normalizeDartCompany(result.company),
    totalCount: result.total_count,
    items: result.items.map(normalizeDartDisclosure),
  };
}

export async function getDartFinancials(
  stockCode: string,
  businessYear = new Date().getFullYear() - 1,
  reportCode = "11011",
): Promise<DartFinancialStatement> {
  const url = new URL(
    `${API_BASE_URL}/dart/companies/${encodeURIComponent(stockCode)}/financials`,
  );
  url.searchParams.set("business_year", String(businessYear));
  url.searchParams.set("report_code", reportCode);
  const result = await request<BackendDartFinancialStatement>(url.toString());
  return {
    company: normalizeDartCompany(result.company),
    businessYear: result.business_year,
    reportCode: result.report_code,
    financialStatementDivision: result.financial_statement_division,
    accounts: result.accounts.map(normalizeDartFinancialAccount),
  };
}

export async function getNews(symbol?: string, limit = 20): Promise<NewsFeed> {
  const url = new URL(`${API_BASE_URL}/news`);
  if (symbol) url.searchParams.set("symbol", symbol);
  url.searchParams.set("limit", String(limit));
  const result = await request<BackendNewsFeed>(url.toString());
  return {
    symbols: result.symbols,
    items: result.items.map(normalizeNewsArticle),
    totalCount: result.total_count,
  };
}

export async function getFinancialHealthAnalysis(
  stockCode: string,
  businessYear = new Date().getFullYear() - 1,
): Promise<FinancialHealthAnalysis> {
  const url = new URL(
    `${API_BASE_URL}/analysis/companies/${encodeURIComponent(stockCode)}/financial-health`,
  );
  url.searchParams.set("business_year", String(businessYear));
  const result = await request<BackendFinancialHealthAnalysis>(url.toString());
  return {
    company: normalizeDartCompany(result.company),
    businessYear: result.business_year,
    reportCode: result.report_code,
    settlementDate: result.settlement_date,
    metrics: result.metrics.map(normalizeFinancialMetric),
    financialRiskScore: result.financial_risk_score,
    financialRiskLevel: result.financial_risk_level,
    evaluatedIndicators: result.evaluated_indicators,
    methodology: result.methodology,
    warnings: result.warnings,
  };
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
