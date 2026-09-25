from fastapi import APIRouter

from backend.app.core.db import get_pool
from backend.app.core.errors import ApiError

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    try:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("select 1")
    except Exception as e:
        raise ApiError(503, "NOT_READY", f"Database unreachable: {e}")
    return {"status": "ok", "db": "ok"}
