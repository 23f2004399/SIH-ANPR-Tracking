from datetime import datetime

import asyncpg


async def list_active_cameras(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "select id, name, latitude, longitude, road_segment_id "
        "from cameras where is_active order by id"
    )
    return [dict(r) for r in rows]


async def count_distinct_tracks(
    conn: asyncpg.Connection, camera_id: str | None, window_start: datetime, window_end: datetime
) -> int:
    """Distinct vehicle_tracks.id seen in this window — a track_id is a real
    primary key, so counting it (not raw observation rows) is what keeps a
    vehicle sitting in frame for several frames from being counted more than
    once."""
    return await conn.fetchval(
        """
        select count(distinct track_id)
        from vehicle_observations
        where observed_at >= $2 and observed_at < $3
          and ($1::text is null or camera_id = $1)
        """,
        camera_id, window_start, window_end,
    )


async def insert_aggregate(
    conn: asyncpg.Connection, camera_id: str | None, segment_id: str | None,
    window_start: datetime, window_end: datetime, metrics: dict,
) -> dict:
    row = await conn.fetchrow(
        """
        insert into traffic_aggregates
            (camera_id, segment_id, window_start, window_end,
             vehicle_count, density_metric, average_speed, congestion_level)
        values ($1, $2, $3, $4, $5, $6, $7, $8)
        returning camera_id, segment_id, window_start, window_end,
                  vehicle_count, density_metric, average_speed, congestion_level, computed_at
        """,
        camera_id, segment_id, window_start, window_end,
        metrics["vehicle_count"], metrics["density_metric"],
        metrics["average_speed"], metrics["congestion_level"],
    )
    return dict(row)


# TODO: GET /traffic/history needs a query here — filter stored
# traffic_aggregates rows by camera_id, segment_id and a date range, with
# limit/offset pagination. Same shape as repositories/jobs.py::list_jobs.
async def list_history(
    conn: asyncpg.Connection,
    camera_id: str | None,
    segment_id: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    limit: int,
    offset: int,
) -> list[dict]:
    rows = await conn.fetch(
        """
        select camera_id, segment_id, window_start, window_end,
               vehicle_count, density_metric, average_speed,
               congestion_level, computed_at
        from traffic_aggregates
        where ($1::text is null or camera_id = $1)
          and ($2::text is null or segment_id = $2)
          and ($3::timestamptz is null or window_start >= $3)
          and ($4::timestamptz is null or window_end <= $4)
        order by window_start desc
        limit $5 offset $6
        """,
        camera_id,
        segment_id,
        start_time,
        end_time,
        limit,
        offset,
    )
    return [dict(r) for r in rows]
