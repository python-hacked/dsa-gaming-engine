import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.middleware.sessions import SessionMiddleware

from dsa_gaming.core.config import ROOT, get_settings
from dsa_gaming.core.logging import configure_logging
from dsa_gaming.modules.gameplay.router import router as gameplay_router
from dsa_gaming.modules.identity.router import router as identity_router
from dsa_gaming.modules.identity.service import build_oauth
from dsa_gaming.presentation.pages import router as pages_router

STATIC_DIR = Path(__file__).resolve().parent / "presentation" / "static"
logger = logging.getLogger(__name__)


def upgrade_database() -> None:
    cfg = Config(str(ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    app.state.sessionmaker = None
    app.state.engine = None
    if settings.database_configured:
        try:
            await asyncio.to_thread(upgrade_database)
            engine = create_async_engine(settings.database_url, pool_pre_ping=True)
            app.state.engine = engine
            app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        except Exception:
            logger.exception("Database is not ready. Sign-in still works from the session.")
    yield
    if app.state.engine is not None:
        await app.state.engine.dispose()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="DSA Gaming Engine", lifespan=lifespan)
    app.state.settings = settings
    app.state.oauth = build_oauth(settings)
    app.state.sessionmaker = None
    app.state.engine = None
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="dsa_session",
        max_age=14 * 24 * 3600,
        same_site="lax",
        https_only=settings.app_env == "production",
    )
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(pages_router)
    app.include_router(identity_router)
    app.include_router(gameplay_router)
    return app


app = create_app()
