from datetime import datetime, timezone

from app.db.database import SQLiteDatabase
from app.schemas.portfolio import Transaction, TransactionCreate


class TransactionRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def list(self, *, symbol: str | None = None) -> list[Transaction]:
        sql = "SELECT * FROM transactions"
        parameters: tuple[str, ...] = ()
        if symbol is not None:
            sql += " WHERE symbol = ?"
            parameters = (symbol,)
        sql += " ORDER BY executed_at DESC, id DESC"

        with self.database.connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, transaction_id: int) -> Transaction | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM transactions WHERE id = ?",
                (transaction_id,),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def create(self, transaction: TransactionCreate) -> Transaction:
        now = datetime.now(timezone.utc).isoformat()
        values = self._values(transaction)
        with self.database.connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO transactions (
                  symbol, transaction_type, quantity, price, currency,
                  fee, tax, executed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*values, now, now),
            )
            transaction_id = cursor.lastrowid
        created = self.get(transaction_id)
        if created is None:
            raise RuntimeError("Created transaction could not be loaded.")
        return created

    def update(
        self,
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
                WHERE id = ?
                """,
                (*values, now, transaction_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get(transaction_id)

    def delete(self, transaction_id: int) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM transactions WHERE id = ?",
                (transaction_id,),
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
