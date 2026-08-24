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
