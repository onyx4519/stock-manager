import io
import zipfile

import httpx
import pytest

from app.providers.dart import DartAPIError, DartConfigurationError, DartProvider


class FakeClient:
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.call_count = 0

    def get(self, url: str, **kwargs) -> httpx.Response:
        self.call_count += 1
        return httpx.Response(
            200,
            content=self.content,
            request=httpx.Request("GET", url),
        )


class RouteClient:
    def __init__(self, payloads: dict[str, dict]) -> None:
        self.payloads = payloads
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, **kwargs) -> httpx.Response:
        self.calls.append((url, kwargs.get("params", {})))
        path = "/" + url.rsplit("/", 1)[-1]
        return httpx.Response(
            200,
            json=self.payloads[path],
            request=httpx.Request("GET", url),
        )


def corp_code_archive() -> bytes:
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<result>
  <list>
    <corp_code>00126380</corp_code>
    <corp_name>삼성전자</corp_name>
    <corp_eng_name>SAMSUNG ELECTRONICS CO.,LTD</corp_eng_name>
    <stock_code>005930</stock_code>
    <modify_date>20260101</modify_date>
  </list>
  <list>
    <corp_code>00000001</corp_code>
    <corp_name>비상장회사</corp_name>
    <corp_eng_name>PRIVATE COMPANY</corp_eng_name>
    <stock_code></stock_code>
    <modify_date>20260102</modify_date>
  </list>
</result>
"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("CORPCODE.xml", xml_data.encode("utf-8"))
    return buffer.getvalue()


def test_find_company_and_cache_corp_codes():
    client = FakeClient(corp_code_archive())
    provider = DartProvider(api_key="test-key", client=client)

    company = provider.find_company(stock_code="005930")
    second_lookup = provider.find_company(corp_name="비상장회사")

    assert company is not None
    assert company["corp_name"] == "삼성전자"
    assert second_lookup is not None
    assert second_lookup["stock_code"] is None
    assert client.call_count == 1


def test_search_listed_companies_excludes_private_companies():
    provider = DartProvider(api_key="test-key", client=FakeClient(corp_code_archive()))

    by_name = provider.search_listed_companies("삼성")
    by_english_name = provider.search_listed_companies("Samsung Electronics")
    by_code = provider.search_listed_companies("005930")
    private = provider.search_listed_companies("비상장")

    assert [item["stock_code"] for item in by_name] == ["005930"]
    assert [item["stock_code"] for item in by_english_name] == ["005930"]
    assert [item["corp_name"] for item in by_code] == ["삼성전자"]
    assert private == []


def test_opendart_error_xml_is_not_treated_as_zip():
    error_xml = (
        "<result><status>010</status>"
        "<message>등록되지 않은 키입니다.</message></result>"
    ).encode("utf-8")
    provider = DartProvider(api_key="invalid-key", client=FakeClient(error_xml))

    with pytest.raises(DartAPIError, match="010"):
        provider.get_corp_codes()


def test_missing_api_key_fails_before_http_request():
    provider = DartProvider(api_key="")

    with pytest.raises(DartConfigurationError, match="DART_API_KEY"):
        provider.get_corp_codes()


def test_disclosures_are_normalized_and_cached():
    client = RouteClient(
        {
            "/list.json": {
                "status": "000",
                "message": "정상",
                "total_count": "1",
                "list": [
                    {
                        "corp_cls": "Y",
                        "corp_name": "삼성전자",
                        "corp_code": "00126380",
                        "stock_code": "005930",
                        "report_nm": "반기보고서 (2026.06)",
                        "rcept_no": "20260814001234",
                        "flr_nm": "삼성전자",
                        "rcept_dt": "20260814",
                        "rm": "연",
                    }
                ],
            }
        }
    )
    provider = DartProvider(api_key="test-key", client=client, cache_seconds=900)

    total, items = provider.search_disclosures("00126380", days=365, limit=20)
    cached_total, cached_items = provider.search_disclosures(
        "00126380", days=365, limit=20
    )

    assert total == cached_total == 1
    assert items == cached_items
    assert items[0]["receipt_date"].isoformat() == "2026-08-14"
    assert items[0]["viewer_url"].endswith("20260814001234")
    assert len(client.calls) == 1
    assert client.calls[0][1]["crtfc_key"] == "test-key"


def test_major_accounts_prefer_consolidated_statements():
    base = {
        "rcept_no": "20260318001234",
        "bsns_year": "2025",
        "reprt_code": "11011",
        "account_nm": "매출액",
        "fs_nm": "연결재무제표",
        "sj_div": "IS",
        "sj_nm": "손익계산서",
        "thstrm_nm": "제57기",
        "thstrm_dt": "2025.01.01 ~ 2025.12.31",
        "thstrm_amount": "300,000",
        "thstrm_add_amount": "",
        "frmtrm_nm": "제56기",
        "frmtrm_dt": "2024.01.01 ~ 2024.12.31",
        "frmtrm_amount": "250,000",
        "currency": "KRW",
    }
    client = RouteClient(
        {
            "/fnlttSinglAcnt.json": {
                "status": "000",
                "message": "정상",
                "list": [
                    {**base, "fs_div": "OFS", "fs_nm": "재무제표"},
                    {**base, "fs_div": "CFS"},
                ],
            }
        }
    )
    provider = DartProvider(api_key="test-key", client=client)

    division, accounts = provider.get_major_accounts(
        "00126380", business_year=2025, report_code="11011"
    )

    assert division == "CFS"
    assert len(accounts) == 1
    assert accounts[0]["current_term_amount"] == 300000
    assert accounts[0]["previous_term_amount"] == 250000


def test_opendart_no_data_status_returns_an_empty_list():
    client = RouteClient(
        {
            "/list.json": {
                "status": "013",
                "message": "조회된 데이터가 없습니다.",
            }
        }
    )
    provider = DartProvider(api_key="test-key", client=client)

    total, items = provider.search_disclosures("00126380")

    assert total == 0
    assert items == []
    assert provider._amount("-") is None
    assert provider._amount("(1,000)") == -1000


class IndicatorClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, **kwargs) -> httpx.Response:
        params = kwargs.get("params", {})
        self.calls.append((url, params))
        category = params["idx_cl_code"]
        code_by_category = {
            "M210000": "M211200",
            "M220000": "M221100",
            "M230000": "M231000",
        }
        value = "13.551" if category == "M210000" else "#########"
        return httpx.Response(
            200,
            json={
                "status": "000",
                "message": "정상",
                "list": [
                    {
                        "reprt_code": "11011",
                        "bsns_year": "2025",
                        "corp_code": "00126380",
                        "stock_code": "005930",
                        "stlm_dt": "2025-12-31",
                        "idx_cl_code": category,
                        "idx_code": code_by_category[category],
                        "idx_val": value,
                    }
                ],
            },
            request=httpx.Request("GET", url),
        )


def test_financial_indicators_are_normalized_by_stable_codes():
    client = IndicatorClient()
    provider = DartProvider(api_key="test-key", client=client)

    indicators = provider.get_financial_indicators(
        "00126380",
        business_year=2025,
    )

    assert len(indicators) == 3
    assert indicators[0]["indicator_code"] == "M211200"
    assert indicators[0]["value"] == 13.551
    assert indicators[1]["value"] is None
    assert {call[1]["idx_cl_code"] for call in client.calls} == {
        "M210000",
        "M220000",
        "M230000",
    }
