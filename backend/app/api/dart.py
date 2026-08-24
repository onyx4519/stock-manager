from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.providers.dart import DartConfigurationError, DartProvider, DartProviderError
from app.schemas.dart import DartCompany


router = APIRouter(prefix="/dart", tags=["dart"])
_provider = DartProvider()


def get_dart_provider() -> DartProvider:
    return _provider


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
    except DartConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DART_API_KEY is not configured.",
        ) from exc
    except DartProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenDART is unavailable or returned invalid data.",
        ) from exc

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DART company not found.",
        )

    return DartCompany.model_validate(company)
