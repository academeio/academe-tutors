"""Database session management — async PostgreSQL via asyncpg."""

import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# asyncpg needs explicit SSL context for Neon pooler connections.
# Strip ssl/sslmode params from URL — pass via connect_args instead.
_db_url = settings.database_url.split("?")[0]
_ssl_ctx = ssl.create_default_context()

engine = create_async_engine(
    _db_url,
    echo=False,
    pool_size=5,
    max_overflow=3,
    pool_pre_ping=True,        # Detect and replace closed connections
    pool_recycle=300,           # Recycle connections every 5 min (Neon pooler timeout)
    connect_args={"ssl": _ssl_ctx},
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with async_session() as session:
        yield session


async def init_db():
    """Run on startup — verify connection. pgvector extension assumed pre-created in Neon."""
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))


async def close_db():
    """Run on shutdown — dispose connection pool."""
    await engine.dispose()
