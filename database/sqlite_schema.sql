CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL COLLATE NOCASE UNIQUE,
  display_name TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_expires
ON sessions(user_id, expires_at);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL CHECK(length(symbol) BETWEEN 1 AND 15),
  transaction_type TEXT NOT NULL CHECK(transaction_type IN ('BUY', 'SELL')),
  quantity TEXT NOT NULL CHECK(CAST(quantity AS REAL) > 0),
  price TEXT NOT NULL CHECK(CAST(price AS REAL) > 0),
  currency TEXT NOT NULL CHECK(length(currency) = 3),
  fee TEXT NOT NULL DEFAULT '0' CHECK(CAST(fee AS REAL) >= 0),
  tax TEXT NOT NULL DEFAULT '0' CHECK(CAST(tax AS REAL) >= 0),
  executed_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_executed_at
ON transactions(executed_at, id);

CREATE INDEX IF NOT EXISTS idx_transactions_symbol_executed_at
ON transactions(symbol, executed_at, id);

CREATE TABLE IF NOT EXISTS watchlist_items (
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL CHECK(length(symbol) BETWEEN 1 AND 15),
  company_name TEXT NOT NULL,
  currency TEXT NOT NULL CHECK(length(currency) = 3),
  created_at TEXT NOT NULL,
  PRIMARY KEY (user_id, symbol)
);
