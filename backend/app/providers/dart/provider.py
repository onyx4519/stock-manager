import io
import copy
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from threading import RLock

import httpx

from app.core.config import settings


class DartProviderError(RuntimeError):
    """Base exception for OpenDART provider failures."""


class DartConfigurationError(DartProviderError):
    """Raised when the OpenDART provider is not configured."""


class DartAPIError(DartProviderError):
    """Raised when OpenDART returns an error or malformed response."""


class DartProvider:
    BASE_URL = "https://opendart.fss.or.kr/api"
    FINANCIAL_INDICATOR_CATEGORIES = ("M210000", "M220000", "M230000")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        cache_seconds: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = settings.dart_api_key if api_key is None else api_key
        self.cache_seconds = (
            settings.dart_cache_seconds if cache_seconds is None else cache_seconds
        )
        self._client = client
        self._companies: tuple[dict[str, str | None], ...] | None = None
        self._payload_cache: dict[
            tuple[str, tuple[tuple[str, str], ...]], tuple[float, dict]
        ] = {}
        self._cache_lock = RLock()

    def get_corp_codes(self) -> list[dict[str, str | None]]:
        """Download and parse OpenDART's corporation-code ZIP file."""
        with self._cache_lock:
            if self._companies is not None:
                return [company.copy() for company in self._companies]

            if not self.api_key:
                raise DartConfigurationError("DART_API_KEY is not configured.")

            request = self._client.get if self._client is not None else httpx.get
            try:
                response = request(
                    f"{self.BASE_URL}/corpCode.xml",
                    params={"crtfc_key": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise DartProviderError(
                    "OpenDART corporation-code request failed."
                ) from exc

            companies = self._parse_corp_code_archive(response.content)
            self._companies = tuple(companies)
            return [company.copy() for company in self._companies]

    def find_company(
        self,
        *,
        corp_name: str | None = None,
        stock_code: str | None = None,
    ) -> dict[str, str | None] | None:
        """Find a company by an exact corporation name or six-digit stock code."""
        normalized_name = corp_name.strip() if corp_name else None
        normalized_stock_code = stock_code.strip() if stock_code else None

        if not normalized_name and not normalized_stock_code:
            raise ValueError("corp_name or stock_code is required.")

        for company in self.get_corp_codes():
            if normalized_stock_code and company["stock_code"] == normalized_stock_code:
                return company
            if normalized_name and company["corp_name"] == normalized_name:
                return company

        return None

    def search_listed_companies(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, str | None]]:
        """Search OpenDART's listed-company directory without extra API calls."""
        term = query.strip().casefold()
        if not term:
            return []

        matches: list[tuple[tuple[int, int, str, str], dict[str, str | None]]] = []
        for company in self.get_corp_codes():
            stock_code = company.get("stock_code")
            if not stock_code:
                continue
            corp_name = company["corp_name"] or ""
            corp_eng_name = company.get("corp_eng_name") or ""
            symbol = stock_code.casefold()
            name = corp_name.casefold()
            english_name = corp_eng_name.casefold()
            if term not in symbol and term not in name and term not in english_name:
                continue

            if term == symbol:
                rank = 0
            elif term == name or term == english_name:
                rank = 1
            elif symbol.startswith(term):
                rank = 2
            elif name.startswith(term) or english_name.startswith(term):
                rank = 3
            else:
                rank = 4
            matches.append(((rank, len(corp_name), corp_name, stock_code), company))

        matches.sort(key=lambda item: item[0])
        return [company.copy() for _, company in matches[:limit]]

    def search_disclosures(
        self,
        corp_code: str,
        *,
        days: int = 365,
        limit: int = 20,
    ) -> tuple[int, list[dict]]:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        payload = self._request_json(
            "/list.json",
            params={
                "corp_code": corp_code,
                "bgn_de": start_date.strftime("%Y%m%d"),
                "end_de": end_date.strftime("%Y%m%d"),
                "last_reprt_at": "Y",
                "sort": "date",
                "sort_mth": "desc",
                "page_no": "1",
                "page_count": str(limit),
            },
            allow_no_data=True,
        )
        rows = self._list(payload)
        items: list[dict] = []
        for row in rows:
            receipt_number = self._required_text(row, "rcept_no")
            receipt_date = self._parse_date(self._required_text(row, "rcept_dt"))
            items.append(
                {
                    "corporation_class": self._required_text(row, "corp_cls"),
                    "corporation_name": self._required_text(row, "corp_name"),
                    "corporation_code": self._required_text(row, "corp_code"),
                    "stock_code": self._optional_text(row, "stock_code"),
                    "report_name": self._required_text(row, "report_nm"),
                    "receipt_number": receipt_number,
                    "filer_name": self._required_text(row, "flr_nm"),
                    "receipt_date": receipt_date,
                    "remarks": self._optional_text(row, "rm"),
                    "viewer_url": (
                        "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="
                        f"{receipt_number}"
                    ),
                }
            )
        total_count = payload.get("total_count", len(items))
        try:
            parsed_total = int(total_count)
        except (TypeError, ValueError) as exc:
            raise DartAPIError("OpenDART disclosure count is invalid.") from exc
        return parsed_total, items

    def get_major_accounts(
        self,
        corp_code: str,
        *,
        business_year: int,
        report_code: str,
    ) -> tuple[str | None, list[dict]]:
        payload = self._request_json(
            "/fnlttSinglAcnt.json",
            params={
                "corp_code": corp_code,
                "bsns_year": str(business_year),
                "reprt_code": report_code,
            },
            allow_no_data=True,
        )
        rows = self._list(payload)
        divisions = {
            self._optional_text(row, "fs_div")
            for row in rows
            if self._optional_text(row, "fs_div")
        }
        preferred_division = "CFS" if "CFS" in divisions else ("OFS" if "OFS" in divisions else None)
        if preferred_division is not None:
            rows = [row for row in rows if row.get("fs_div") == preferred_division]

        accounts: list[dict] = []
        for row in rows:
            accounts.append(
                {
                    "receipt_number": self._required_text(row, "rcept_no"),
                    "business_year": self._required_text(row, "bsns_year"),
                    "report_code": self._required_text(row, "reprt_code"),
                    "account_name": self._required_text(row, "account_nm"),
                    "financial_statement_division": self._required_text(row, "fs_div"),
                    "financial_statement_name": self._required_text(row, "fs_nm"),
                    "statement_division": self._required_text(row, "sj_div"),
                    "statement_name": self._required_text(row, "sj_nm"),
                    "current_term_name": self._optional_text(row, "thstrm_nm"),
                    "current_term_date": self._optional_text(row, "thstrm_dt"),
                    "current_term_amount": self._amount(row.get("thstrm_amount")),
                    "current_term_cumulative_amount": self._amount(
                        row.get("thstrm_add_amount")
                    ),
                    "previous_term_name": self._optional_text(row, "frmtrm_nm"),
                    "previous_term_date": self._optional_text(row, "frmtrm_dt"),
                    "previous_term_amount": self._amount(row.get("frmtrm_amount")),
                    "currency": self._optional_text(row, "currency"),
                }
            )
        return preferred_division, accounts

    def get_financial_indicators(
        self,
        corp_code: str,
        *,
        business_year: int,
        report_code: str = "11011",
    ) -> list[dict]:
        indicators: list[dict] = []
        for category_code in self.FINANCIAL_INDICATOR_CATEGORIES:
            payload = self._request_json(
                "/fnlttSinglIndx.json",
                params={
                    "corp_code": corp_code,
                    "bsns_year": str(business_year),
                    "reprt_code": report_code,
                    "idx_cl_code": category_code,
                },
                allow_no_data=True,
            )
            for row in self._list(payload):
                indicators.append(
                    {
                        "report_code": self._required_text(row, "reprt_code"),
                        "business_year": self._required_text(row, "bsns_year"),
                        "corporation_code": self._required_text(row, "corp_code"),
                        "stock_code": self._optional_text(row, "stock_code"),
                        "settlement_date": self._optional_text(row, "stlm_dt"),
                        "category_code": self._required_text(row, "idx_cl_code"),
                        "indicator_code": self._required_text(row, "idx_code"),
                        "value": self._indicator_value(row.get("idx_val")),
                    }
                )
        return indicators

    def _request_json(
        self,
        path: str,
        *,
        params: dict[str, str],
        allow_no_data: bool = False,
    ) -> dict:
        if not self.api_key:
            raise DartConfigurationError("DART_API_KEY is not configured.")

        request_params = {"crtfc_key": self.api_key, **params}
        cache_key = (path, tuple(sorted(params.items())))
        with self._cache_lock:
            cached = self._payload_cache.get(cache_key)
            now = time.monotonic()
            if cached is not None and now - cached[0] < self.cache_seconds:
                return copy.deepcopy(cached[1])

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
                raise DartProviderError("OpenDART JSON request failed.") from exc

            if not isinstance(payload, dict):
                raise DartAPIError("OpenDART returned a non-object JSON response.")
            status = payload.get("status")
            if status == "013" and allow_no_data:
                payload = {**payload, "list": []}
            elif status != "000":
                raise DartAPIError("OpenDART returned an error status.")

            self._payload_cache[cache_key] = (now, copy.deepcopy(payload))
            return payload

    @staticmethod
    def _list(payload: dict) -> list[dict]:
        rows = payload.get("list", [])
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise DartAPIError("OpenDART list response is invalid.")
        return rows

    @staticmethod
    def _required_text(row: dict, key: str) -> str:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise DartAPIError(f"OpenDART field {key!r} is missing.")
        return value.strip()

    @staticmethod
    def _optional_text(row: dict, key: str) -> str | None:
        value = row.get(key)
        return value.strip() or None if isinstance(value, str) else None

    @staticmethod
    def _parse_date(value: str) -> date:
        try:
            return datetime.strptime(value, "%Y%m%d").date()
        except ValueError as exc:
            raise DartAPIError("OpenDART date is invalid.") from exc

    @staticmethod
    def _amount(value: object) -> int | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise DartAPIError("OpenDART amount is invalid.")
        normalized = str(value).strip().replace(",", "")
        if not normalized or normalized in {"-", "N/A"}:
            return None
        is_parenthesized = normalized.startswith("(") and normalized.endswith(")")
        if is_parenthesized:
            normalized = f"-{normalized[1:-1]}"
        try:
            return int(normalized)
        except ValueError as exc:
            raise DartAPIError("OpenDART amount is invalid.") from exc

    @staticmethod
    def _indicator_value(value: object) -> float | None:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise DartAPIError("OpenDART indicator value is invalid.")
        normalized = str(value).strip().replace(",", "")
        if not normalized or normalized in {"-", "N/A"} or "#" in normalized:
            return None
        try:
            return float(normalized)
        except ValueError as exc:
            raise DartAPIError("OpenDART indicator value is invalid.") from exc

    @classmethod
    def _parse_corp_code_archive(
        cls,
        content: bytes,
    ) -> list[dict[str, str | None]]:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                file_name = next(
                    name for name in archive.namelist() if name.upper() == "CORPCODE.XML"
                )
                xml_data = archive.read(file_name)
        except (StopIteration, KeyError, zipfile.BadZipFile) as exc:
            raise cls._response_error(content) from exc

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as exc:
            raise DartAPIError("OpenDART corporation-code XML is invalid.") from exc

        companies: list[dict[str, str | None]] = []
        for item in root.findall("list"):
            corp_code = (item.findtext("corp_code") or "").strip()
            corp_name = (item.findtext("corp_name") or "").strip()
            if not corp_code or not corp_name:
                raise DartAPIError("OpenDART corporation-code data is incomplete.")

            companies.append(
                {
                    "corp_code": corp_code,
                    "corp_name": corp_name,
                    "corp_eng_name": (item.findtext("corp_eng_name") or "").strip() or None,
                    "stock_code": (item.findtext("stock_code") or "").strip() or None,
                    "modify_date": (item.findtext("modify_date") or "").strip() or None,
                }
            )

        return companies

    @staticmethod
    def _response_error(content: bytes) -> DartAPIError:
        try:
            root = ET.fromstring(content)
            status = (root.findtext("status") or "").strip()
            message = (root.findtext("message") or "").strip()
        except ET.ParseError:
            status = ""
            message = ""

        if status or message:
            detail = ": ".join(part for part in (status, message) if part)
            return DartAPIError(f"OpenDART returned an error ({detail}).")

        return DartAPIError(
            "OpenDART returned content that is not a corporation-code ZIP file."
        )
