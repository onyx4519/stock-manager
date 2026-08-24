from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dart import get_dart_provider
from app.providers.dart import DartConfigurationError, DartProvider, DartProviderError
from app.schemas.analysis import FinancialHealthAnalysis
from app.schemas.dart import DartCompany
from app.services.financial_analysis_service import FinancialAnalysisService


router = APIRouter(prefix="/analysis", tags=["analysis"])
service = FinancialAnalysisService()


def _raise_dart_error(exc: DartProviderError) -> None:
    if isinstance(exc, DartConfigurationError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DART_API_KEY is not configured.",
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="OpenDART is unavailable or returned invalid data.",
    ) from exc


@router.get(
    "/companies/{stock_code}/financial-health",
    response_model=FinancialHealthAnalysis,
)
def get_financial_health(
    stock_code: Annotated[str, Path(pattern=r"^\d{6}$")],
    provider: Annotated[DartProvider, Depends(get_dart_provider)],
    business_year: Annotated[int, Query(ge=2023, le=date.today().year)] = (
        date.today().year - 1
    ),
) -> FinancialHealthAnalysis:
    try:
        company_data = provider.find_company(stock_code=stock_code)
        if company_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DART company not found.",
            )
        indicators = provider.get_financial_indicators(
            company_data["corp_code"],
            business_year=business_year,
            report_code="11011",
        )
    except DartProviderError as exc:
        _raise_dart_error(exc)

    return service.analyze(
        company=DartCompany.model_validate(company_data),
        business_year=business_year,
        indicators=indicators,
    )
