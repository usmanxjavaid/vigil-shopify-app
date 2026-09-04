from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

# Neon's pooler (PgBouncer) doesn't support asyncpg's per-connection
# prepared-statement caching reliably — statement_cache_size=0 disables
# it. pool_pre_ping=True checks a connection is genuinely still alive
# before handing it out — Neon suspends/closes idle connections fairly
# aggressively, and without this, any gap of inactivity between requests
# (a few seconds is enough) surfaces as "connection is closed" on the
# next query, the way it just did.
engine = create_async_engine(
    settings.database_url,
    connect_args={"ssl": "require", "statement_cache_size": 0},
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields one session per request, always closed
    afterward via `async with`, even if the request raised an error.
    """
    async with AsyncSessionLocal() as session:
        yield session