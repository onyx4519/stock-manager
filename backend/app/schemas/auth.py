from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserCredentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        local, separator, domain = normalized.partition("@")
        if not separator or not local or "." not in domain:
            raise ValueError("A valid email address is required.")
        return normalized


class UserRegister(UserCredentials):
    display_name: str = Field(min_length=2, max_length=50)
    personalization_consent: bool = False

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("display_name must contain at least two characters.")
        return normalized


class AuthUser(BaseModel):
    id: str
    email: str
    display_name: str
    personalization_consent: bool = False
    personalization_consent_at: datetime | None = None
    created_at: datetime


class AuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: AuthUser


class AccountDeletionReason(StrEnum):
    MISSING_CONTENT = "MISSING_CONTENT"
    DIFFICULT_TO_USE = "DIFFICULT_TO_USE"
    DATA_QUALITY = "DATA_QUALITY"
    PRIVACY_CONCERN = "PRIVACY_CONCERN"
    NO_LONGER_NEEDED = "NO_LONGER_NEEDED"
    NO_REASON = "NO_REASON"


class AccountDeletionRequest(BaseModel):
    confirmed: Literal[True]
    reason: AccountDeletionReason
