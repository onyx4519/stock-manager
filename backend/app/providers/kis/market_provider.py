import re
import time
from datetime import date, datetime, time as datetime_time, timedelta
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


class KisMarketProvider:
    BASE_URLS = {
        "real": "https://openapi.koreainvestment.com:9443",
        "demo": "https://openapivts.koreainvestment.com:29443",
    }
    SYMBOL_PATTERN = re.compile(r"^\d{6}$")
    SEOUL_TZ = ZoneInfo("Asia/Seoul")

    def __init__(
        self,
        *,
        app_key: str | None = None,
        app_secret: str | None = None,
        symbols: tuple[str, ...] | None = None,
        environment: str | None = None,
        cache_seconds: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.app_key = settings.kis_app_key if app_key is None else app_key
        self.app_secret = (
            settings.kis_app_secret if app_secret is None else app_secret
        )
        self.symbols = settings.kis_symbols if symbols is None else symbols
        self.environment = (
            settings.kis_environment if environment is None else environment
        )
        if self.environment not in self.BASE_URLS:
            raise ValueError("KIS environment must be 'real' or 'demo'.")
        self.base_url = self.BASE_URLS[self.environment]
        self.cache_seconds = (
            settings.kis_cache_seconds if cache_seconds is None else cache_seconds
        )
        self._client = client
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._quotes: dict[str, tuple[float, StockQuote]] = {}
        self._lock = RLock()

    def list_quotes(self) -> list[StockQuote]:
        quotes: list[StockQuote] = []
        for symbol in self.symbols:
            quote = self.get_quote(symbol)
            if quote is not None:
                quotes.append(quote)
        return quotes

    def get_quote(self, symbol: str) -> StockQuote | None:
        normalized_symbol = symbol.strip()
        if not self.SYMBOL_PATTERN.fullmatch(normalized_symbol):
            return None
        self._validate_configuration()

        with self._lock:
            cached = self._quotes.get(normalized_symbol)
            now = time.monotonic()
            if cached is not None and now - cached[0] < self.cache_seconds:
                return cached[1].model_copy()

            payload = self._get_daily_chart(normalized_symbol)
            quote = self._normalize_quote(normalized_symbol, payload)
            self._quotes[normalized_symbol] = (now, quote)
            return quote.model_copy()

    def _validate_configuration(self) -> None:
        if not self.app_key or not self.app_secret:
            raise MarketProviderConfigurationError(
                "KIS_APP_KEY or KIS_APP_SECRET is not configured."
            )

    def _get_access_token(self) -> str:
        now = time.monotonic()
        if self._access_token is not None and now < self._token_expires_at:
            return self._access_token

        payload = self._request_token()
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise MarketProviderDataError("KIS access token is missing.")

        expires_in = self._positive_number(payload.get("expires_in", 86400))
        self._access_token = access_token.strip()
        self._token_expires_at = now + max(expires_in - 60, 1)
        return self._access_token

    def _request_token(self) -> dict:
        request = self._client.post if self._client is not None else httpx.post
        try:
            response = request(
                f"{self.base_url}/oauth2/tokenP",
                headers={"content-type": "application/json"},
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MarketProviderError("KIS token request failed.") from exc

        if not isinstance(payload, dict):
            raise MarketProviderDataError("KIS token response is invalid.")
        return payload

    def _get_daily_chart(self, symbol: str, *, retry: bool = True) -> dict:
        end_date = datetime.now(self.SEOUL_TZ).date() - timedelta(days=1)
        start_date = end_date - timedelta(days=14)
        token = self._get_access_token()
        request = self._client.get if self._client is not None else httpx.get

        try:
            response = request(
                f"{self.base_url}/uapi/domestic-stock/v1/quotations/"
                "inquire-daily-itemchartprice",
                headers={
                    "content-type": "application/json",
                    "authorization": f"Bearer {token}",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                    "tr_id": "FHKST03010100",
                },
                params={
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": symbol,
                    "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": end_date.strftime("%Y%m%d"),
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MarketProviderError("KIS market-data request failed.") from exc

        if not isinstance(payload, dict):
            raise MarketProviderDataError("KIS market-data response is invalid.")
        if payload.get("rt_cd") != "0":
            if retry and payload.get("msg_cd") == "EGW00123":
                self._access_token = None
                self._token_expires_at = 0.0
                return self._get_daily_chart(symbol, retry=False)
            raise MarketProviderError("KIS returned an error status.")
        return payload

    def _normalize_quote(self, symbol: str, payload: dict) -> StockQuote:
        summary = payload.get("output1")
        bars = payload.get("output2")
        if not isinstance(summary, dict) or not isinstance(bars, list):
            raise MarketProviderDataError("KIS daily chart data is missing.")

        company_name = summary.get("hts_kor_isnm")
        if not isinstance(company_name, str) or not company_name.strip():
            raise MarketProviderDataError("KIS company name is missing.")

        parsed_bars: list[tuple[date, float]] = []
        for bar in bars:
            if not isinstance(bar, dict):
                raise MarketProviderDataError("KIS daily bar is invalid.")
            date_text = bar.get("stck_bsop_date")
            if not isinstance(date_text, str):
                raise MarketProviderDataError("KIS daily bar date is invalid.")
            try:
                bar_date = datetime.strptime(date_text, "%Y%m%d").date()
            except ValueError as exc:
                raise MarketProviderDataError(
                    "KIS daily bar date is invalid."
                ) from exc
            close = self._positive_number(bar.get("stck_clpr"))
            parsed_bars.append((bar_date, close))

        parsed_bars.sort(key=lambda item: item[0])
        if len(parsed_bars) < 2:
            raise MarketProviderDataError(
                "KIS returned fewer than two completed daily bars."
            )

        previous_date, previous_close = parsed_bars[-2]
        latest_date, latest_close = parsed_bars[-1]
        if latest_date <= previous_date:
            raise MarketProviderDataError("KIS daily bars are not chronological.")

        change_percent = ((latest_close - previous_close) / previous_close) * 100
        timestamp = datetime.combine(
            latest_date,
            datetime_time(hour=15, minute=30),
            tzinfo=self.SEOUL_TZ,
        )
        return StockQuote(
            symbol=symbol,
            company_name=company_name.strip(),
            price=latest_close,
            change_percent=round(change_percent, 4),
            currency="KRW",
            timestamp=timestamp,
            data_status=DataStatus.EOD,
            provider="KIS",
        )

    @staticmethod
    def _positive_number(value: object) -> float:
        if isinstance(value, bool):
            raise MarketProviderDataError("KIS numeric field is invalid.")
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise MarketProviderDataError("KIS numeric field is invalid.") from exc
        if number <= 0:
            raise MarketProviderDataError("KIS numeric field must be positive.")
        return number
