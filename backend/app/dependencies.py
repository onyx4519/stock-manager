from app.core.config import settings
from app.db import SQLiteDatabase, TransactionRepository
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.transaction_service import TransactionService


market_service = MarketService()
database = SQLiteDatabase(settings.database_path)
transaction_repository = TransactionRepository(database)
transaction_service = TransactionService(transaction_repository, market_service)
portfolio_service = PortfolioService(transaction_repository, market_service)
