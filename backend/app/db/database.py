import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "database" / "sqlite_schema.sql"


class SQLiteDatabase:
    LEGACY_USER_ID = "legacy-local-user"

    def __init__(self, path: Path) -> None:
        self.path = path
        self._initialized = False
        self._initialization_lock = Lock()

    def initialize(self) -> None:
        if self._initialized:
            return

        with self._initialization_lock:
            if self._initialized:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            schema = SCHEMA_PATH.read_text(encoding="utf-8")
            with self._open() as connection:
                connection.execute("PRAGMA journal_mode = WAL")
                connection.execute("PRAGMA foreign_keys = ON")
                connection.executescript(schema)
                self._migrate_user_ownership(connection)
                connection.execute("PRAGMA optimize")
            self._initialized = True

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.initialize()
        connection = self._open()
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10.0)
        connection.row_factory = sqlite3.Row
        return connection

    def _migrate_user_ownership(self, connection: sqlite3.Connection) -> None:
        now = "1970-01-01T00:00:00+00:00"
        connection.execute(
            """
            INSERT OR IGNORE INTO users (
              id, email, display_name, password_hash, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                self.LEGACY_USER_ID,
                "legacy@local.invalid",
                "기존 로컬 데이터",
                "!legacy",
                now,
            ),
        )

        transaction_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info('transactions')")
        }
        if "user_id" not in transaction_columns:
            connection.execute(
                """
                ALTER TABLE transactions
                ADD COLUMN user_id TEXT NOT NULL DEFAULT 'legacy-local-user'
                """
            )

        watchlist_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info('watchlist_items')")
        }
        if "user_id" not in watchlist_columns:
            connection.execute("DROP INDEX IF EXISTS idx_watchlist_items_created_at")
            connection.execute(
                "ALTER TABLE watchlist_items RENAME TO watchlist_items_legacy"
            )
            connection.execute(
                """
                CREATE TABLE watchlist_items (
                  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                  symbol TEXT NOT NULL CHECK(length(symbol) BETWEEN 1 AND 15),
                  company_name TEXT NOT NULL,
                  currency TEXT NOT NULL CHECK(length(currency) = 3),
                  created_at TEXT NOT NULL,
                  PRIMARY KEY (user_id, symbol)
                )
                """
            )
            connection.execute(
                """
                INSERT INTO watchlist_items (
                  user_id, symbol, company_name, currency, created_at
                )
                SELECT ?, symbol, company_name, currency, created_at
                FROM watchlist_items_legacy
                """,
                (self.LEGACY_USER_ID,),
            )
            connection.execute("DROP TABLE watchlist_items_legacy")

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_user_executed_at
            ON transactions(user_id, executed_at DESC, id DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_user_symbol_executed_at
            ON transactions(user_id, symbol, executed_at, id)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_watchlist_items_created_at
            ON watchlist_items(user_id, created_at DESC, symbol)
            """
        )
