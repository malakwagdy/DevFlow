import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import CompanyRole, UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # UUIDs serialize to plain strings in JSON.
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    company_id: uuid.UUID | None
    company_role: CompanyRole | None
    created_at: datetime
