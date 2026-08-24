from app.core.config import settings
from app.db import SQLiteDatabase, TransactionRepository, WatchlistRepository
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.transaction_service import TransactionService
from app.services.watchlist_service import WatchlistService


market_service = MarketService()
database = SQLiteDatabase(settings.database_path)
transaction_repository = TransactionRepository(database)
watchlist_repository = WatchlistRepository(database)
transaction_service = TransactionService(transaction_repository, market_service)
portfolio_service = PortfolioService(transaction_repository, market_service)
watchlist_service = WatchlistService(watchlist_repository, market_service)
