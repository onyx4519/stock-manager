import io
import zipfile
import xml.etree.ElementTree as ET

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

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = settings.dart_api_key if api_key is None else api_key
        self._client = client
        self._companies: tuple[dict[str, str | None], ...] | None = None

    def get_corp_codes(self) -> list[dict[str, str | None]]:
        """Download and parse OpenDART's corporation-code ZIP file."""
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
            raise DartProviderError("OpenDART corporation-code request failed.") from exc

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
