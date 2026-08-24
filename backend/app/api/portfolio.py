from fastapi import APIRouter
from app.dependencies import portfolio_service as service
from app.schemas.portfolio import PortfolioSummary, Position

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/positions", response_model=list[Position])
def list_positions() -> list[Position]:
    return service.list_positions()


@router.get("/summary", response_model=PortfolioSummary)
def get_summary() -> PortfolioSummary:
    return service.get_summary()
