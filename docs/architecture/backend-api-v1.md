# Backend API v1

Base URL: `/api/v1`

## Health
- `GET /health`
- Purpose: server health + mock mode state.

## Stocks
- `GET /api/v1/stocks?q={query}`
- Searches by company name or symbol in the current provider.
- Searches the symbols configured through `KIS_SYMBOLS` and `MASSIVE_SYMBOLS`.
- Every result keeps its provider and data-status label.

## Watchlist
- `GET /api/v1/watchlist`
- `POST /api/v1/watchlist`
- `DELETE /api/v1/watchlist/{symbol}`

Watchlist symbols persist in SQLite. Additions are validated against the configured market providers, duplicates are rejected, and the list is enriched with the latest available quote when read.

## Market
- `GET /api/v1/market/quotes`
- `GET /api/v1/market/quotes/{symbol}`
- Every quote includes timestamp, provider, currency, and `data_status`.
- `MARKET_PROVIDER=mock` preserves the existing development data.
- `MARKET_PROVIDER=massive` loads configured U.S. symbols from `MASSIVE_SYMBOLS`.
- `MARKET_PROVIDER=kis` loads configured Korean symbols from `KIS_SYMBOLS`.
- `MARKET_PROVIDER=hybrid` routes six-digit Korean symbols to KIS and English tickers to Massive.
- Massive and KIS quotes use completed daily data and are explicitly marked `EOD`; no realtime status is inferred.

## Portfolio
- `GET /api/v1/portfolio/positions`
- `GET /api/v1/portfolio/summary`

Positions are rebuilt from the SQLite transaction ledger and current provider quotes. Summary values are separated by currency instead of applying an implicit exchange rate.

## Transactions
- `GET /api/v1/transactions`
- `GET /api/v1/transactions/{id}`
- `POST /api/v1/transactions`
- `PATCH /api/v1/transactions/{id}`
- `DELETE /api/v1/transactions/{id}`

Transactions persist in SQLite. The API rejects unsupported symbols, currency mismatches, and any change that would make the historical position quantity negative.

## OpenDART
- `GET /api/v1/dart/companies/search?stock_code={six-digit-code}`
- `GET /api/v1/dart/companies/search?corp_name={exact-name}`
- `GET /api/v1/dart/companies/{stock_code}/disclosures?days=365&limit=20`
- `GET /api/v1/dart/companies/{stock_code}/financials?business_year={year}&report_code=11011`

The corporation-code archive and JSON responses are fetched through the backend and cached in memory. Disclosure results include official DART viewer links. Major accounts prefer consolidated statements (`CFS`) and fall back to separate statements (`OFS`). OpenDART's no-data status (`013`) becomes an empty result rather than a server error. The API returns `503` when `DART_API_KEY` is missing, `502` for upstream or response errors, and `404` when no exact company match exists.

## Design rules
1. Frontend never calls market vendors directly.
2. Provider responses are normalized before UI use.
3. Mock/Delayed/Realtime/EOD states are explicit.
4. Financial calculations live in deterministic calculation modules, not in AI output.
5. A missing external value stays missing; it is not synthesized.
