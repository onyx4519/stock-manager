from app.db.auth_repository import AuthRepository, DuplicateUserError
from app.db.notification_repository import NotificationRepository
from app.schemas.auth import (
    AccountDeletionReason,
    AuthSession,
    AuthUser,
    UserCredentials,
    UserRegister,
)
from app.schemas.notifications import NotificationCategory


class InvalidCredentialsError(ValueError):
    pass


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        notification_repository: NotificationRepository | None = None,
    ) -> None:
        self.repository = repository
        self.notification_repository = notification_repository

    def register(self, payload: UserRegister) -> AuthSession:
        user = self.repository.create_user(
            email=str(payload.email),
            display_name=payload.display_name,
            password=payload.password,
            birth_date=payload.birth_date,
            gender=payload.gender,
            account_creation_consent=payload.account_creation_consent,
            privacy_collection_consent=payload.privacy_collection_consent,
            personalization_consent=payload.personalization_consent,
            service_notification_consent=payload.service_notification_consent,
        )
        if self.notification_repository is not None:
            self.notification_repository.create_for_user(
                user_id=user.id,
                notification_key=f"welcome:{user.id}",
                category=NotificationCategory.ACCOUNT,
                title="가입이 완료되었습니다",
                message="Stock Manager 계정이 생성되었습니다.",
            )
        return self._create_session(user)

    def login(self, payload: UserCredentials) -> AuthSession:
        user = self.repository.verify_credentials(str(payload.email), payload.password)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password.")
        return self._create_session(user)

    def authenticate(self, token: str) -> AuthUser | None:
        return self.repository.get_user_by_session(token)

    def logout(self, token: str) -> None:
        self.repository.delete_session(token)

    def delete_account(self, user_id: str, reason: AccountDeletionReason) -> bool:
        return self.repository.delete_user(user_id, reason)

    def update_notification_preference(
        self,
        user_id: str,
        enabled: bool,
    ) -> AuthUser:
        user = self.repository.update_service_notification_consent(user_id, enabled)
        if user is None:
            raise LookupError("Account not found.")
        return user

    def _create_session(self, user: AuthUser) -> AuthSession:
        token, expires_at = self.repository.create_session(user.id)
        return AuthSession(access_token=token, expires_at=expires_at, user=user)


__all__ = [
    "AuthService",
    "DuplicateUserError",
    "InvalidCredentialsError",
]
