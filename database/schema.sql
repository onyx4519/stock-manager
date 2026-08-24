-- Stock Manager MVP core schema (PostgreSQL / Supabase-ready)
-- Designed so provider data, user transactions, and calculated positions remain separate.

create extension if not exists pgcrypto;

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  name_ko text,
  country text not null,
  sector text,
  industry text,
  description text,
  website text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists securities (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id),
  security_type text not null default 'common_stock',
  share_class text,
  isin text,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists listings (
  id uuid primary key default gen_random_uuid(),
  security_id uuid not null references securities(id),
  ticker text not null,
  exchange text not null,
  country text not null,
  currency text not null,
  timezone text not null,
  status text not null default 'active',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(exchange, ticker)
);

create table if not exists provider_mappings (
  id uuid primary key default gen_random_uuid(),
  listing_id uuid not null references listings(id),
  provider text not null,
  provider_symbol text not null,
  provider_exchange text,
  metadata jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(provider, provider_symbol, provider_exchange)
);

create table if not exists market_quotes (
  id bigserial primary key,
  listing_id uuid not null references listings(id),
  provider text not null,
  price numeric(30,10) not null check(price >= 0),
  change numeric(30,10),
  change_percent numeric(20,8),
  volume numeric(30,8),
  currency text not null,
  market_session text,
  data_status text not null,
  quoted_at timestamptz not null,
  received_at timestamptz not null default now()
);

create index if not exists idx_market_quotes_listing_time on market_quotes(listing_id, quoted_at desc);

create table if not exists portfolios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  name text not null default '기본 포트폴리오',
  base_currency text not null default 'KRW',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists transactions (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references portfolios(id),
  listing_id uuid not null references listings(id),
  transaction_type text not null check(transaction_type in ('BUY','SELL')),
  quantity numeric(30,10) not null check(quantity > 0),
  price numeric(30,10) not null check(price > 0),
  currency text not null,
  fee numeric(30,10) not null default 0 check(fee >= 0),
  tax numeric(30,10) not null default 0 check(tax >= 0),
  fx_rate numeric(30,10) check(fx_rate > 0),
  executed_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);

create index if not exists idx_transactions_portfolio_listing_time on transactions(portfolio_id, listing_id, executed_at);

create table if not exists positions (
  id uuid primary key default gen_random_uuid(),
  portfolio_id uuid not null references portfolios(id),
  listing_id uuid not null references listings(id),
  quantity numeric(30,10) not null default 0,
  average_cost numeric(30,10) not null default 0,
  cost_basis numeric(30,10) not null default 0,
  realized_pnl numeric(30,10) not null default 0,
  calculated_at timestamptz not null default now(),
  calculation_version text not null default 'v1',
  unique(portfolio_id, listing_id)
);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  title text not null,
  summary text,
  source text,
  source_url text,
  published_at timestamptz,
  occurred_at timestamptz,
  importance text,
  verification_status text not null default 'unverified',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
