import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# "owner/repo" using GitHub's allowed characters. Validated strictly because it
# is interpolated into the GitHub API URL.
REPO_FULL_NAME_PATTERN = r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$"


class ProjectCreate(BaseModel):
    repo_full_name: str = Field(
        pattern=REPO_FULL_NAME_PATTERN,
        examples=["octocat/hello-world"],
    )
    # Default to the repository's name and description when omitted.
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("repo_full_name")
    @classmethod
    def reject_dot_segments(cls, value: str) -> str:
        if value.split("/", 1)[1] in {".", ".."}:
            raise ValueError("Invalid repository name")
        return value


class ProjectUpdate(BaseModel):
    """Only the fields sent are changed. `description: null` clears it."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def name_cannot_be_cleared(self) -> Self:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    repo_url: str | None
    repo_full_name: str
    default_branch: str
    is_private: bool
    owner_id: uuid.UUID
    team_id: uuid.UUID | None
    created_at: datetime
