from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.github import router as github_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.session import router as session_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import AppError, InvalidTokenError, NotAuthenticatedError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Schema is managed by Alembic (`alembic upgrade head`), not created here.
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="DevFlow", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(github_router)
    application.include_router(projects_router)
    application.include_router(session_router)
    application.include_router(users_router)
    application.add_exception_handler(AppError, _app_error_handler)
    return application


async def _app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    headers = dict(exc.headers or {})
    if isinstance(exc, (InvalidTokenError, NotAuthenticatedError)):
        headers["WWW-Authenticate"] = "Bearer"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers or None,
    )


app = create_app()
