from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.dependencies import portfolio_service as service
from app.schemas.auth import AuthUser
from app.schemas.portfolio import PortfolioSummary, Position

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/positions", response_model=list[Position])
def list_positions(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> list[Position]:
    return service.list_positions(user.id)


@router.get("/summary", response_model=PortfolioSummary)
def get_summary(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> PortfolioSummary:
    return service.get_summary(user.id)
