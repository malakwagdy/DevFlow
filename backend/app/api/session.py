import re
import unicodedata

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.models.company import Company
from app.schemas.session import SessionResponse, SessionUser, SessionWorkspace

router = APIRouter(prefix="/session", tags=["session"])


def initials(name: str) -> str:
    """"Alex Vance" -> "AV"; a single word gives its first two letters."""
    words = name.split()
    if not words:
        return ""
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[-1][0]).upper()


def slugify(name: str) -> str:
    """"Acme Production" -> "acme-production". Empty if nothing ASCII is left."""
    ascii_name = (
        unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


@router.get("", status_code=status.HTTP_200_OK, response_model=SessionResponse)
async def get_session(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> SessionResponse:
    workspace = None
    if current_user.company_id is not None:
        # Loaded explicitly: lazy-loading the relationship isn't allowed in async.
        company = await session.get(Company, current_user.company_id)
        if company is not None:
            workspace = SessionWorkspace(
                # Fall back to the id for names with no ASCII letters (e.g. Arabic).
                slug=slugify(company.name) or str(company.id),
                name=company.name,
                initials=initials(company.name),
            )

    return SessionResponse(
        user=SessionUser(
            name=current_user.full_name,
            initials=initials(current_user.full_name),
            email=current_user.email,
        ),
        workspace=workspace,
    )
