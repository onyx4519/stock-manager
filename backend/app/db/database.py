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
                self._migrate_basic_profile(connection)
                self._migrate_account_creation_consent(connection)
                self._migrate_privacy_and_notification_consents(connection)
                self._migrate_personalization_consent(connection)
                self._migrate_account_deletion_feedback(connection)
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

    @staticmethod
    def _migrate_basic_profile(connection: sqlite3.Connection) -> None:
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info('users')")
        }
        if "birth_date" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN birth_date TEXT")
        if "gender" not in user_columns:
            connection.execute(
                """
                ALTER TABLE users ADD COLUMN gender TEXT NOT NULL
                DEFAULT 'UNSPECIFIED'
                CHECK(gender IN ('UNSPECIFIED', 'MALE', 'FEMALE'))
                """
            )

    @staticmethod
    def _migrate_account_creation_consent(
        connection: sqlite3.Connection,
    ) -> None:
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info('users')")
        }
        if "account_creation_consent_at" not in user_columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN account_creation_consent_at TEXT"
            )
        if "account_creation_consent_version" not in user_columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN account_creation_consent_version TEXT"
            )

    @staticmethod
    def _migrate_privacy_and_notification_consents(
        connection: sqlite3.Connection,
    ) -> None:
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info('users')")
        }
        additions = {
            "privacy_collection_consent_at": "TEXT",
            "privacy_collection_consent_version": "TEXT",
            "service_notification_consent": (
                "INTEGER NOT NULL DEFAULT 0 CHECK(service_notification_consent IN (0, 1))"
            ),
            "service_notification_consent_at": "TEXT",
            "service_notification_consent_version": "TEXT",
        }
        for column, definition in additions.items():
            if column not in user_columns:
                connection.execute(
                    f"ALTER TABLE users ADD COLUMN {column} {definition}"
                )

    @staticmethod
    def _migrate_personalization_consent(
        connection: sqlite3.Connection,
    ) -> None:
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info('users')")
        }
        if "personalization_consent" not in user_columns:
            connection.execute(
                """
                ALTER TABLE users ADD COLUMN personalization_consent
                INTEGER NOT NULL DEFAULT 0
                CHECK(personalization_consent IN (0, 1))
                """
            )
        if "personalization_consent_at" not in user_columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN personalization_consent_at TEXT"
            )
        if "personalization_consent_version" not in user_columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN personalization_consent_version TEXT"
            )

    @staticmethod
    def _migrate_account_deletion_feedback(
        connection: sqlite3.Connection,
    ) -> None:
        table = connection.execute(
            """
            SELECT sql FROM sqlite_schema
            WHERE type = 'table' AND name = 'account_deletion_feedback'
            """
        ).fetchone()
        if table is None or "'NO_REASON'" in table["sql"]:
            return

        connection.execute(
            """
            ALTER TABLE account_deletion_feedback
            RENAME TO account_deletion_feedback_legacy
            """
        )
        connection.execute(
            """
            CREATE TABLE account_deletion_feedback (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              reason TEXT NOT NULL CHECK(reason IN (
                'MISSING_CONTENT',
                'DIFFICULT_TO_USE',
                'DATA_QUALITY',
                'PRIVACY_CONCERN',
                'NO_LONGER_NEEDED',
                'NO_REASON'
              )),
              created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO account_deletion_feedback (id, reason, created_at)
            SELECT id, reason, created_at
            FROM account_deletion_feedback_legacy
            """
        )
        connection.execute("DROP TABLE account_deletion_feedback_legacy")
