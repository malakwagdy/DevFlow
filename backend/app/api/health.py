import asyncio
import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.dependencies import SessionDep

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

DB_CHECK_TIMEOUT_SECONDS = 2.0


@router.get("", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Is the process up? Deliberately ignores the database, so a Postgres
    outage doesn't make Docker restart a perfectly healthy API in a loop."""
    return {"status": "ok"}


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unreachable"}},
)
async def readiness(session: SessionDep) -> JSONResponse:
    """Can the API serve requests? Used after deploys and by monitoring."""
    try:
        await asyncio.wait_for(
            session.execute(text("SELECT 1")),
            timeout=DB_CHECK_TIMEOUT_SECONDS,
        )
    except Exception:
        # Details go to the server log only; the response stays generic.
        logger.exception("Readiness check failed: database unreachable")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "unavailable"},
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok", "database": "ok"},
    )
