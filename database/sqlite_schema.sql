CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
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
