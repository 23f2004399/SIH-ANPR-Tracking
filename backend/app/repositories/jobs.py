import asyncpg

from backend.app.schemas.job import JobIn


async def create_job(conn: asyncpg.Connection, job: JobIn) -> dict:
    row = await conn.fetchrow(
        """
        insert into processing_jobs (camera_id, source_file_key)
        values ($1, $2)
        returning id, camera_id, source_file_key, status, progress,
                  started_at, completed_at, error_message, created_at
        """,
        job.camera_id, job.source_file_key,
    )
    return dict(row)


async def get_job(conn: asyncpg.Connection, job_id: int) -> dict | None:
    row = await conn.fetchrow(
        "select id, camera_id, source_file_key, status, progress, "
        "started_at, completed_at, error_message, created_at "
        "from processing_jobs where id = $1",
        job_id,
    )
    return dict(row) if row else None


async def list_jobs(conn: asyncpg.Connection, camera_id: str | None, status: str | None,
                     limit: int, offset: int) -> list[dict]:
    rows = await conn.fetch(
        """
        select id, camera_id, source_file_key, status, progress,
               started_at, completed_at, error_message, created_at
        from processing_jobs
        where ($1::text is null or camera_id = $1)
          and ($2::text is null or status = $2)
        order by created_at desc
        limit $3 offset $4
        """,
        camera_id, status, limit, offset,
    )
    return [dict(r) for r in rows]
