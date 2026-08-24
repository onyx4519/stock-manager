import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Iterator


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "database" / "sqlite_schema.sql"


class SQLiteDatabase:
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
