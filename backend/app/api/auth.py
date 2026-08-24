from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import auth_service as service
from app.schemas.auth import AuthSession, AuthUser, UserCredentials, UserRegister
from app.services.auth_service import DuplicateUserError, InvalidCredentialsError


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


def get_current_user(token: Annotated[str, Depends(get_session_token)]) -> AuthUser:
    user = service.authenticate(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired.",
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
def me(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(token: Annotated[str, Depends(get_session_token)]) -> None:
    service.logout(token)
