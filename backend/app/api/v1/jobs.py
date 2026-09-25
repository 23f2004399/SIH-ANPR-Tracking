from fastapi import APIRouter, Query

from backend.app.core.db import get_pool
from backend.app.core.errors import ApiError, envelope
from backend.app.repositories import jobs as repo
from backend.app.schemas.job import JobIn

router = APIRouter()


@router.post("/jobs")
async def create_job(job: JobIn):
    async with get_pool().acquire() as conn:
        row = await repo.create_job(conn, job)
    return envelope(row)


@router.get("/jobs/{job_id}")
async def get_job(job_id: int):
    async with get_pool().acquire() as conn:
        row = await repo.get_job(conn, job_id)
    if row is None:
        raise ApiError(404, "RESOURCE_NOT_FOUND", f"Job {job_id} not found")
    return envelope(row)


@router.get("/jobs")
async def list_jobs(
    camera_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    async with get_pool().acquire() as conn:
        rows = await repo.list_jobs(conn, camera_id, status, limit, offset)
    return envelope(rows)
