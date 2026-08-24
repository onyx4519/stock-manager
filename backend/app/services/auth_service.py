from app.db.auth_repository import AuthRepository, DuplicateUserError
from app.schemas.auth import (
    AccountDeletionReason,
    AuthSession,
    AuthUser,
    UserCredentials,
    UserRegister,
)


class InvalidCredentialsError(ValueError):
    pass


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

    def register(self, payload: UserRegister) -> AuthSession:
        user = self.repository.create_user(
            email=str(payload.email),
            display_name=payload.display_name,
            password=payload.password,
            personalization_consent=payload.personalization_consent,
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

    def _create_session(self, user: AuthUser) -> AuthSession:
        token, expires_at = self.repository.create_session(user.id)
        return AuthSession(access_token=token, expires_at=expires_at, user=user)


__all__ = [
    "AuthService",
    "DuplicateUserError",
    "InvalidCredentialsError",
]
