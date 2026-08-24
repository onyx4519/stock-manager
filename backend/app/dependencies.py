from app.core.config import settings
from app.db import (
    AdminRepository,
    AuthRepository,
    NotificationRepository,
    SQLiteDatabase,
    TransactionRepository,
    WatchlistRepository,
)
from app.services.auth_service import AuthService
from app.services.market_service import MarketService
from app.services.notification_service import NotificationService
from app.services.stock_directory_service import StockDirectoryService
from app.services.portfolio_service import PortfolioService
from app.services.transaction_service import TransactionService
from app.services.watchlist_service import WatchlistService


market_service = MarketService()
stock_directory_service = StockDirectoryService(market_service)
database = SQLiteDatabase(settings.database_path)
admin_repository = AdminRepository(database)
auth_repository = AuthRepository(database)
notification_repository = NotificationRepository(database)
auth_service = AuthService(auth_repository, notification_repository)
notification_service = NotificationService(notification_repository)
transaction_repository = TransactionRepository(database)
watchlist_repository = WatchlistRepository(database)
transaction_service = TransactionService(transaction_repository, market_service)
portfolio_service = PortfolioService(transaction_repository, market_service)
watchlist_service = WatchlistService(watchlist_repository, market_service)
