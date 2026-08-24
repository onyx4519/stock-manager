from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import auth_service as service
from app.schemas.auth import (
    AccountDeletionRequest,
    AuthSession,
    AuthUser,
    NotificationPreferenceUpdate,
    PasswordChangeRequest,
    UserCredentials,
    UserRegister,
    UserRole,
)
from app.services.auth_service import (
    DuplicateUserError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    PasswordPolicyError,
)


router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def get_session_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
) -> str:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return credentials.credentials


def get_authenticated_user(
    token: Annotated[str, Depends(get_session_token)],
) -> AuthUser:
    user = service.authenticate(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired.",
        )
    return user


def get_current_user(
    user: Annotated[AuthUser, Depends(get_authenticated_user)],
) -> AuthUser:
    if user.password_change_required:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required.",
        )
    return user


def get_current_admin(
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> AuthUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission required.",
        )
    return user


@router.post("/register", response_model=AuthSession, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister) -> AuthSession:
    try:
        return service.register(payload)
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail="Email is already registered.") from exc


@router.post("/login", response_model=AuthSession)
def login(payload: UserCredentials) -> AuthSession:
    try:
        return service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password.") from exc


@router.get("/me", response_model=AuthUser)
def me(user: Annotated[AuthUser, Depends(get_authenticated_user)]) -> AuthUser:
    return user


@router.get("/admin/me", response_model=AuthUser)
def admin_me(user: Annotated[AuthUser, Depends(get_current_admin)]) -> AuthUser:
    return user


@router.patch("/preferences/notifications", response_model=AuthUser)
def update_notification_preference(
    payload: NotificationPreferenceUpdate,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> AuthUser:
    try:
        return service.update_notification_preference(
            user.id,
            payload.service_notification_consent,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Account not found.") from exc


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    user: Annotated[AuthUser, Depends(get_authenticated_user)],
) -> None:
    try:
        service.change_password(
            user,
            payload.current_password,
            payload.new_password,
        )
    except InvalidCurrentPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is invalid.",
        ) from exc
    except PasswordPolicyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: Annotated[str, Depends(get_session_token)]) -> None:
    service.logout(token)


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: AccountDeletionRequest,
    user: Annotated[AuthUser, Depends(get_current_user)],
) -> None:
    if not service.delete_account(user.id, payload.reason):
        raise HTTPException(status_code=404, detail="Account not found.")
