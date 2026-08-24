from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.portfolio import Transaction, TransactionCreate


class TransactionRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def list(self, user_id: str, *, symbol: str | None = None) -> list[Transaction]:
        sql = "SELECT * FROM transactions WHERE user_id = ?"
        parameters: tuple[str, ...] = (user_id,)
        if symbol is not None:
            sql += " AND symbol = ?"
            parameters = (user_id, symbol)
        sql += " ORDER BY executed_at DESC, id DESC"

        with self.database.connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, user_id: str, transaction_id: int) -> Transaction | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM transactions WHERE user_id = ? AND id = ?",
                (user_id, transaction_id),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def create(self, user_id: str, transaction: TransactionCreate) -> Transaction:
        now = datetime.now(timezone.utc).isoformat()
        values = self._values(transaction)
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO transactions (
                  user_id, symbol, transaction_type, quantity, price, currency,
                  fee, tax, executed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, *values, now, now),
            )
            transaction_id = cursor.lastrowid
        created = self.get(user_id, transaction_id)
        if created is None:
            raise RuntimeError("Created transaction could not be loaded.")
        return created

    def update(
        self,
        user_id: str,
        transaction_id: int,
        transaction: TransactionCreate,
    ) -> Transaction | None:
        now = datetime.now(timezone.utc).isoformat()
        values = self._values(transaction)
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE transactions
                SET symbol = ?, transaction_type = ?, quantity = ?, price = ?,
                    currency = ?, fee = ?, tax = ?, executed_at = ?, updated_at = ?
                WHERE user_id = ? AND id = ?
                """,
                (*values, now, user_id, transaction_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get(user_id, transaction_id)

    def delete(self, user_id: str, transaction_id: int) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM transactions WHERE user_id = ? AND id = ?",
                (user_id, transaction_id),
            )
        return cursor.rowcount > 0

    @staticmethod
    def _values(transaction: TransactionCreate) -> tuple[str, ...]:
        return (
            transaction.symbol,
            transaction.transaction_type.value,
            str(transaction.quantity),
            str(transaction.price),
            transaction.currency,
            str(transaction.fee),
            str(transaction.tax),
            transaction.executed_at.astimezone(timezone.utc).isoformat(),
        )

    @staticmethod
    def _from_row(row) -> Transaction:
        return Transaction.model_validate(dict(row))
