from fastapi import APIRouter
from app.schemas.portfolio import Position, TransactionCreate
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
service = PortfolioService()


@router.get("/positions", response_model=list[Position])
def list_positions() -> list[Position]:
    return service.list_positions()


@router.post("/transactions", status_code=201)
def create_transaction(transaction: TransactionCreate):
    # Persistence is deliberately not faked. This endpoint validates the contract only until DB is connected.
    return {"status": "accepted_mock_only", "transaction": transaction}
