import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from app.db.database import SQLiteDatabase
from app.schemas.auth import AuthUser


class DuplicateUserError(ValueError):
    pass


class AuthRepository:
    PASSWORD_ITERATIONS = 600_000
    SESSION_DAYS = 30

    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
    ) -> AuthUser:
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password)
        try:
            with self.database.connection() as connection:
                real_users = connection.execute(
                    "SELECT COUNT(*) FROM users WHERE id != ?",
                    (self.database.LEGACY_USER_ID,),
                ).fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO users (
                      id, email, display_name, password_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, email.casefold(), display_name, password_hash, created_at),
                )
                if real_users == 0:
                    connection.execute(
                        "UPDATE transactions SET user_id = ? WHERE user_id = ?",
                        (user_id, self.database.LEGACY_USER_ID),
                    )
                    connection.execute(
                        "UPDATE watchlist_items SET user_id = ? WHERE user_id = ?",
                        (user_id, self.database.LEGACY_USER_ID),
                    )
        except sqlite3.IntegrityError as exc:
            raise DuplicateUserError("Email is already registered.") from exc

        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("Created user could not be loaded.")
        return user

    def verify_credentials(self, email: str, password: str) -> AuthUser | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, password_hash, created_at
                FROM users
                WHERE email = ? COLLATE NOCASE AND id != ?
                """,
                (email.casefold(), self.database.LEGACY_USER_ID),
            ).fetchone()
        if row is None or not self._verify_password(password, row["password_hash"]):
            return None
        return AuthUser.model_validate(dict(row))

    def get_user(self, user_id: str) -> AuthUser | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, created_at
                FROM users WHERE id = ? AND id != ?
                """,
                (user_id, self.database.LEGACY_USER_ID),
            ).fetchone()
        return AuthUser.model_validate(dict(row)) if row is not None else None

    def create_session(self, user_id: str) -> tuple[str, datetime]:
        token = secrets.token_urlsafe(32)
        token_hash = self._token_hash(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.SESSION_DAYS)
        with self.database.connection() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE expires_at <= ?",
                (now.isoformat(),),
            )
            connection.execute(
                """
                INSERT INTO sessions (token_hash, user_id, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (token_hash, user_id, expires_at.isoformat(), now.isoformat()),
            )
        return token, expires_at

    def get_user_by_session(self, token: str) -> AuthUser | None:
        token_hash = self._token_hash(token)
        now = datetime.now(timezone.utc).isoformat()
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT users.id, users.email, users.display_name, users.created_at
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = ? AND sessions.expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
        return AuthUser.model_validate(dict(row)) if row is not None else None

    def delete_session(self, token: str) -> None:
        with self.database.connection() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (self._token_hash(token),),
            )

    @classmethod
    def _hash_password(cls, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.PASSWORD_ITERATIONS,
        )
        return (
            f"pbkdf2_sha256${cls.PASSWORD_ITERATIONS}$"
            f"{salt.hex()}${digest.hex()}"
        )

    @staticmethod
    def _verify_password(password: str, encoded: str) -> bool:
        try:
            algorithm, iterations_text, salt_hex, expected_hex = encoded.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations_text),
            )
        except (ValueError, TypeError):
            return False
        return secrets.compare_digest(digest.hex(), expected_hex)

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
