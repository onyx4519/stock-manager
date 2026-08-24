# Backend API v1

Base URL: `/api/v1`

## Health
- `GET /health`
- Purpose: server health + mock mode state.

## Stocks
- `GET /api/v1/stocks?q={query}`
- Searches by company name or symbol in the current provider.
- MVP response uses clearly tagged Mock data.

## Market
- `GET /api/v1/market/quotes`
- `GET /api/v1/market/quotes/{symbol}`
- Every quote includes timestamp, provider, currency, and `data_status`.

## Portfolio
- `GET /api/v1/portfolio/positions`
- `POST /api/v1/portfolio/transactions`

The POST endpoint currently validates the request contract only. It does not pretend to persist data before PostgreSQL/Supabase is connected.

## OpenDART
- `GET /api/v1/dart/companies/search?stock_code={six-digit-code}`
- `GET /api/v1/dart/companies/search?corp_name={exact-name}`

The corporation-code archive is fetched through the backend and cached in memory. The API returns `503` when `DART_API_KEY` is missing, `502` for upstream or response errors, and `404` when no exact match exists.

## Design rules
1. Frontend never calls market vendors directly.
2. Provider responses are normalized before UI use.
3. Mock/Delayed/Realtime/EOD states are explicit.
4. Financial calculations live in deterministic calculation modules, not in AI output.
5. A missing external value stays missing; it is not synthesized.
