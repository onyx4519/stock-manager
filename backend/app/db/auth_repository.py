import hashlib
import secrets
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone

from app.db.database import SQLiteDatabase
from app.schemas.auth import AccountDeletionReason, AuthUser, Gender, UserRole


class DuplicateUserError(ValueError):
    pass


class AuthRepository:
    PASSWORD_ITERATIONS = 600_000
    ACCOUNT_CREATION_CONSENT_VERSION = "2026-08-25-v1"
    PRIVACY_COLLECTION_CONSENT_VERSION = "2026-08-25-v1"
    PERSONALIZATION_CONSENT_VERSION = "2026-08-25-v1"
    SERVICE_NOTIFICATION_CONSENT_VERSION = "2026-08-25-v1"
    SESSION_DAYS = 30

    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def create_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str,
        birth_date: date | None = None,
        gender: Gender = Gender.UNSPECIFIED,
        role: UserRole = UserRole.USER,
        claim_legacy_data: bool = True,
        account_creation_consent: bool = False,
        privacy_collection_consent: bool = False,
        personalization_consent: bool = False,
        service_notification_consent: bool = False,
    ) -> AuthUser:
        user_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        account_consented_at = created_at if account_creation_consent else None
        account_consent_version = (
            self.ACCOUNT_CREATION_CONSENT_VERSION
            if account_creation_consent
            else None
        )
        privacy_consented_at = created_at if privacy_collection_consent else None
        privacy_consent_version = (
            self.PRIVACY_COLLECTION_CONSENT_VERSION
            if privacy_collection_consent
            else None
        )
        consented_at = created_at if personalization_consent else None
        consent_version = (
            self.PERSONALIZATION_CONSENT_VERSION
            if personalization_consent
            else None
        )
        notification_consented_at = (
            created_at if service_notification_consent else None
        )
        notification_consent_version = (
            self.SERVICE_NOTIFICATION_CONSENT_VERSION
            if service_notification_consent
            else None
        )
        password_hash = self._hash_password(password)
        try:
            with self.database.connection() as connection:
                user_accounts = connection.execute(
                    "SELECT COUNT(*) FROM users WHERE id != ? AND role = 'USER'",
                    (self.database.LEGACY_USER_ID,),
                ).fetchone()[0]
                connection.execute(
                    """
                    INSERT INTO users (
                      id, email, display_name, password_hash,
                      birth_date, gender, role,
                      account_creation_consent_at,
                      account_creation_consent_version,
                      privacy_collection_consent_at,
                      privacy_collection_consent_version,
                      personalization_consent, personalization_consent_at,
                      personalization_consent_version,
                      service_notification_consent,
                      service_notification_consent_at,
                      service_notification_consent_version,
                      created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        email.casefold(),
                        display_name,
                        password_hash,
                        birth_date.isoformat() if birth_date is not None else None,
                        gender.value,
                        role.value,
                        account_consented_at,
                        account_consent_version,
                        privacy_consented_at,
                        privacy_consent_version,
                        int(personalization_consent),
                        consented_at,
                        consent_version,
                        int(service_notification_consent),
                        notification_consented_at,
                        notification_consent_version,
                        created_at,
                    ),
                )
                if user_accounts == 0 and claim_legacy_data:
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

    def verify_credentials(
        self,
        email: str,
        password: str,
    ) -> tuple[AuthUser | None, int | None]:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, password_hash, birth_date, gender, role,
                       failed_login_attempts, password_change_required,
                       personalization_consent, personalization_consent_at,
                       service_notification_consent,
                       service_notification_consent_at,
                       created_at
                FROM users
                WHERE email = ? COLLATE NOCASE AND id != ?
                """,
                (email.casefold(), self.database.LEGACY_USER_ID),
            ).fetchone()
            if row is None:
                return None, None
            if not self._verify_password(password, row["password_hash"]):
                failed_attempts = min(int(row["failed_login_attempts"]) + 1, 5)
                connection.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = ?,
                        password_change_required = CASE
                          WHEN ? >= 5 THEN 1
                          ELSE password_change_required
                        END,
                        last_failed_login_at = ?
                    WHERE id = ?
                    """,
                    (
                        failed_attempts,
                        failed_attempts,
                        datetime.now(timezone.utc).isoformat(),
                        row["id"],
                    ),
                )
                return None, failed_attempts
            if not row["password_change_required"]:
                connection.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = 0, last_failed_login_at = NULL
                    WHERE id = ?
                    """,
                    (row["id"],),
                )
            return AuthUser.model_validate(dict(row)), 0

    def get_user(self, user_id: str) -> AuthUser | None:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT id, email, display_name, birth_date, gender, role,
                       password_change_required,
                       personalization_consent,
                       personalization_consent_at,
                       service_notification_consent,
                       service_notification_consent_at, created_at
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
                SELECT users.id, users.email, users.display_name,
                       users.birth_date, users.gender, users.role,
                       users.password_change_required,
                       users.personalization_consent,
                       users.personalization_consent_at,
                       users.service_notification_consent,
                       users.service_notification_consent_at,
                       users.created_at
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

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        with self.database.connection() as connection:
            row = connection.execute(
                """
                SELECT password_hash FROM users
                WHERE id = ? AND id != ?
                """,
                (user_id, self.database.LEGACY_USER_ID),
            ).fetchone()
            if row is None or not self._verify_password(
                current_password,
                row["password_hash"],
            ):
                return False
            connection.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    failed_login_attempts = 0,
                    password_change_required = 0,
                    last_failed_login_at = NULL
                WHERE id = ?
                """,
                (self._hash_password(new_password), user_id),
            )
            connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        return True

    def update_service_notification_consent(
        self,
        user_id: str,
        enabled: bool,
    ) -> AuthUser | None:
        consented_at = datetime.now(timezone.utc).isoformat() if enabled else None
        consent_version = (
            self.SERVICE_NOTIFICATION_CONSENT_VERSION if enabled else None
        )
        with self.database.connection() as connection:
            result = connection.execute(
                """
                UPDATE users
                SET service_notification_consent = ?,
                    service_notification_consent_at = ?,
                    service_notification_consent_version = ?
                WHERE id = ? AND id != ?
                """,
                (
                    int(enabled),
                    consented_at,
                    consent_version,
                    user_id,
                    self.database.LEGACY_USER_ID,
                ),
            )
        return self.get_user(user_id) if result.rowcount == 1 else None

    def delete_user(self, user_id: str, reason: AccountDeletionReason) -> bool:
        deleted_at = datetime.now(timezone.utc).isoformat()
        with self.database.connection() as connection:
            result = connection.execute(
                "DELETE FROM users WHERE id = ? AND id != ?",
                (user_id, self.database.LEGACY_USER_ID),
            )
            if result.rowcount != 1:
                return False
            connection.execute(
                """
                INSERT INTO account_deletion_feedback (reason, created_at)
                VALUES (?, ?)
                """,
                (reason.value, deleted_at),
            )
        return True

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
