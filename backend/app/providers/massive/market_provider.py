import re
import time
from datetime import datetime, timedelta, timezone
from threading import RLock
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings
from app.providers.market import (
    MarketProviderConfigurationError,
    MarketProviderDataError,
    MarketProviderError,
)
from app.schemas.market import DataStatus, StockQuote


class MassiveMarketProvider:
    BASE_URL = "https://api.massive.com"
    SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,14}$")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        symbols: tuple[str, ...] | None = None,
        cache_seconds: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = settings.massive_api_key if api_key is None else api_key
        self.symbols = settings.massive_symbols if symbols is None else symbols
        self.cache_seconds = (
            settings.massive_cache_seconds if cache_seconds is None else cache_seconds
        )
        self._client = client
        self._company_names: dict[str, tuple[str, str]] = {}
        self._quotes: dict[str, tuple[float, StockQuote]] = {}
        self._cache_lock = RLock()

    def list_quotes(self) -> list[StockQuote]:
        quotes: list[StockQuote] = []
        for symbol in self.symbols:
            quote = self.get_quote(symbol)
            if quote is not None:
                quotes.append(quote)
        return quotes

    def get_quote(self, symbol: str) -> StockQuote | None:
        normalized_symbol = symbol.strip().upper()
        if not self.SYMBOL_PATTERN.fullmatch(normalized_symbol):
            return None
        if not self.api_key:
            raise MarketProviderConfigurationError(
                "MASSIVE_API_KEY is not configured."
            )

        with self._cache_lock:
            cached = self._quotes.get(normalized_symbol)
            now = time.monotonic()
            if cached is not None and now - cached[0] < self.cache_seconds:
                return cached[1].model_copy()

            company_name, currency = self._get_company_metadata(normalized_symbol)
            bars = self._get_recent_daily_bars(normalized_symbol)
            if not bars:
                return None
            if len(bars) < 2:
                raise MarketProviderDataError(
                    "Massive returned fewer than two completed daily bars."
                )

            previous_close = self._number(bars[-2], "c")
            latest_close = self._number(bars[-1], "c")
            timestamp_ms = self._number(bars[-1], "t")
            if previous_close <= 0:
                raise MarketProviderDataError("Massive returned an invalid close price.")

            change_percent = ((latest_close - previous_close) / previous_close) * 100
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)

            quote = StockQuote(
                symbol=normalized_symbol,
                company_name=company_name,
                price=latest_close,
                change_percent=round(change_percent, 4),
                currency=currency,
                timestamp=timestamp,
                data_status=DataStatus.EOD,
                provider="Massive",
            )
            self._quotes[normalized_symbol] = (now, quote)
            return quote.model_copy()

    def _get_company_metadata(self, symbol: str) -> tuple[str, str]:
        cached = self._company_names.get(symbol)
        if cached is not None:
            return cached

        payload = self._request_json(f"/v3/reference/tickers/{symbol}")
        result = payload.get("results")
        if not isinstance(result, dict):
            raise MarketProviderDataError("Massive ticker details are missing.")

        name = result.get("name")
        currency_name = result.get("currency_name")
        if not isinstance(name, str) or not name.strip():
            raise MarketProviderDataError("Massive ticker name is missing.")
        if not isinstance(currency_name, str) or not currency_name.strip():
            raise MarketProviderDataError("Massive ticker currency is missing.")

        metadata = (name.strip(), currency_name.strip().upper())
        self._company_names[symbol] = metadata
        return metadata

    def _get_recent_daily_bars(self, symbol: str) -> list[dict]:
        eastern_today = datetime.now(ZoneInfo("America/New_York")).date()
        end_date = eastern_today - timedelta(days=1)
        start_date = end_date - timedelta(days=10)
        payload = self._request_json(
            f"/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}",
            params={"adjusted": "true", "sort": "asc", "limit": 10},
        )
        results = payload.get("results")
        if results is None:
            return []
        if not isinstance(results, list) or not all(
            isinstance(item, dict) for item in results
        ):
            raise MarketProviderDataError("Massive daily bars are invalid.")
        return results

    def _request_json(self, path: str, *, params: dict | None = None) -> dict:
        request_params = dict(params or {})
        request_params["apiKey"] = self.api_key
        request = self._client.get if self._client is not None else httpx.get

        try:
            response = request(
                f"{self.BASE_URL}{path}",
                params=request_params,
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MarketProviderError("Massive request failed.") from exc

        if not isinstance(payload, dict):
            raise MarketProviderDataError("Massive returned a non-object response.")
        if payload.get("status") not in {"OK", "DELAYED"}:
            raise MarketProviderError("Massive returned an error status.")
        return payload

    @staticmethod
    def _number(item: dict, key: str) -> float:
        value = item.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise MarketProviderDataError(
                f"Massive daily bar field {key!r} is invalid."
            )
        return float(value)
