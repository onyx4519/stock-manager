import sqlite3
from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.market import StockQuote
from app.schemas.watchlist import WatchlistRecord


class DuplicateWatchlistItemError(ValueError):
    pass


class WatchlistRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def list(self, user_id: str) -> list[WatchlistRecord]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT symbol, company_name, currency, created_at
                FROM watchlist_items
                WHERE user_id = ?
                ORDER BY created_at DESC, symbol
                """,
                (user_id,),
            ).fetchall()
        return [WatchlistRecord.model_validate(dict(row)) for row in rows]

    def get(self, user_id: str, symbol: str) -> WatchlistRecord | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT symbol, company_name, currency, created_at
                FROM watchlist_items
                WHERE user_id = ? AND symbol = ?
                """,
                (user_id, symbol),
            ).fetchone()
        return WatchlistRecord.model_validate(dict(row)) if row is not None else None

    def create(self, user_id: str, quote: StockQuote) -> WatchlistRecord:
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with self.database.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO watchlist_items (
                      user_id, symbol, company_name, currency, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, quote.symbol, quote.company_name, quote.currency, created_at),
                )
        except sqlite3.IntegrityError as exc:
            raise DuplicateWatchlistItemError(
                f"{quote.symbol} is already in the watchlist."
            ) from exc

        created = self.get(user_id, quote.symbol)
        if created is None:
            raise RuntimeError("Created watchlist item could not be loaded.")
        return created

    def delete(self, user_id: str, symbol: str) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM watchlist_items WHERE user_id = ? AND symbol = ?",
                (user_id, symbol),
            )
        return cursor.rowcount > 0
