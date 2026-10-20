from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole
    # Optional: when given, a company is created with this user as its owner,
    # plus one default team containing the owner.
    company_name: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("full_name", "company_name", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("role")
    @classmethod
    def reject_admin_registration(cls, value: UserRole) -> UserRole:
        if value is UserRole.admin:
            raise ValueError("Public registration cannot create an admin user")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
