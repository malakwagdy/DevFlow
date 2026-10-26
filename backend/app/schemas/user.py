import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.user import CompanyRole, UserRole

# Rules for any password a user sets (register, reset, change).
NewPassword = Annotated[str, Field(min_length=8, max_length=128)]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # UUIDs serialize to plain strings in JSON.
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    email_verified: bool
    company_id: uuid.UUID | None
    company_role: CompanyRole | None
    created_at: datetime


class UserUpdate(BaseModel):
    """PATCH /users/me: only the fields sent change. Changing the email needs
    the current password, so a stolen access token can't take over the account."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    current_password: str | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def check_fields(self) -> Self:
        for field in ("full_name", "email"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if self.email is not None and not self.current_password:
            raise ValueError("current_password is required to change the email")
        return self


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: NewPassword

    @model_validator(mode="after")
    def must_differ(self) -> Self:
        if self.new_password == self.current_password:
            raise ValueError("new_password must be different from current_password")
        return self


class AccountDeleteRequest(BaseModel):
    password: str
