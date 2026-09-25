import asyncpg

from backend.app.core.config import settings

pool: asyncpg.Pool | None = None


async def connect():
    global pool
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set")
    pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)


async def disconnect():
    global pool
    if pool is not None:
        await pool.close()
        pool = None


def get_pool() -> asyncpg.Pool:
    if pool is None:
        raise RuntimeError("DB pool not initialised — did the app start up?")
    return pool
