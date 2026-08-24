from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.providers.dart import DartConfigurationError, DartProvider, DartProviderError
from app.schemas.dart import (
    DartCompany,
    DartDisclosureList,
    DartFinancialStatement,
)


router = APIRouter(prefix="/dart", tags=["dart"])
_provider = DartProvider()


def get_dart_provider() -> DartProvider:
    return _provider


def _raise_provider_error(exc: DartProviderError) -> None:
    if isinstance(exc, DartConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DART_API_KEY is not configured.",
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="OpenDART is unavailable or returned invalid data.",
    ) from exc


def _find_company_or_404(provider: DartProvider, stock_code: str) -> DartCompany:
    try:
        company = provider.find_company(stock_code=stock_code)
    except DartProviderError as exc:
        _raise_provider_error(exc)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DART company not found.",
        )
    return DartCompany.model_validate(company)


@router.get("/companies/search", response_model=DartCompany)
def find_company(
    provider: Annotated[DartProvider, Depends(get_dart_provider)],
    corp_name: Annotated[str | None, Query(min_length=1)] = None,
    stock_code: Annotated[str | None, Query(pattern=r"^\d{6}$")] = None,
) -> DartCompany:
    if not corp_name and not stock_code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="corp_name or stock_code is required.",
        )

    try:
        company = provider.find_company(corp_name=corp_name, stock_code=stock_code)
    except DartProviderError as exc:
        _raise_provider_error(exc)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DART company not found.",
        )

    return DartCompany.model_validate(company)


@router.get(
    "/companies/{stock_code}/disclosures",
    response_model=DartDisclosureList,
)
def list_company_disclosures(
    stock_code: Annotated[str, Path(pattern=r"^\d{6}$")],
    provider: Annotated[DartProvider, Depends(get_dart_provider)],
    days: Annotated[int, Query(ge=1, le=3650)] = 365,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DartDisclosureList:
    company = _find_company_or_404(provider, stock_code)
    try:
        total_count, items = provider.search_disclosures(
            company.corp_code,
            days=days,
            limit=limit,
        )
    except DartProviderError as exc:
        _raise_provider_error(exc)
    return DartDisclosureList(
        company=company,
        total_count=total_count,
        items=items,
    )


@router.get(
    "/companies/{stock_code}/financials",
    response_model=DartFinancialStatement,
)
def get_company_financials(
    stock_code: Annotated[str, Path(pattern=r"^\d{6}$")],
    provider: Annotated[DartProvider, Depends(get_dart_provider)],
    business_year: Annotated[int, Query(ge=2015, le=date.today().year)] = (
        date.today().year - 1
    ),
    report_code: Literal["11011", "11012", "11013", "11014"] = "11011",
) -> DartFinancialStatement:
    company = _find_company_or_404(provider, stock_code)
    try:
        division, accounts = provider.get_major_accounts(
            company.corp_code,
            business_year=business_year,
            report_code=report_code,
        )
    except DartProviderError as exc:
        _raise_provider_error(exc)
    return DartFinancialStatement(
        company=company,
        business_year=str(business_year),
        report_code=report_code,
        financial_statement_division=division,
        accounts=accounts,
    )
