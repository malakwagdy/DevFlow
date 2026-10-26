from pydantic import BaseModel, EmailStr


class SessionUser(BaseModel):
    name: str
    initials: str
    email: EmailStr


class SessionWorkspace(BaseModel):
    slug: str
    name: str
    initials: str
    # No deployment target exists yet; always null until deployments are built.
    cluster: str | None = None


class SessionResponse(BaseModel):
    """What the app shell needs on load: who is signed in and their workspace
    (company). `workspace` is null for users without a company."""

    user: SessionUser
    workspace: SessionWorkspace | None
