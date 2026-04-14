"""Academe Tutors — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Academe Tutors",
    description="LTI-deployable AI tutoring for CBME",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Route registration ---

from app.api.routers import health, lti, chat, knowledge  # noqa: E402

app.include_router(health.router, tags=["health"])
app.include_router(lti.router, prefix="/lti", tags=["lti"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
