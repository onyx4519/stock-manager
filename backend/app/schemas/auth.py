from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


class Gender(StrEnum):
    UNSPECIFIED = "UNSPECIFIED"
    MALE = "MALE"
    FEMALE = "FEMALE"


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"


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
    birth_date: date
    gender: Gender = Gender.UNSPECIFIED
    account_creation_consent: Literal[True]
    privacy_collection_consent: Literal[True]
    personalization_consent: bool = False
    service_notification_consent: bool = False

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("display_name must contain at least two characters.")
        return normalized

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value < date(1900, 1, 1):
            raise ValueError("birth_date must be on or after 1900-01-01.")
        if value > datetime.now(ZoneInfo("Asia/Seoul")).date():
            raise ValueError("birth_date cannot be in the future.")
        return value


class AuthUser(BaseModel):
    id: str
    email: str
    display_name: str
    birth_date: date | None = None
    gender: Gender = Gender.UNSPECIFIED
    role: UserRole = UserRole.USER
    personalization_consent: bool = False
    personalization_consent_at: datetime | None = None
    service_notification_consent: bool = False
    service_notification_consent_at: datetime | None = None
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


class NotificationPreferenceUpdate(BaseModel):
    service_notification_consent: bool
