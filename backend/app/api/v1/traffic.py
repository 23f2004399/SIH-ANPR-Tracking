from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from backend.app.core.db import get_pool
from backend.app.core.errors import ApiError,envelope
from backend.app.repositories import traffic as repo
from backend.app.services.analytics.aggregation import compute_metrics

router = APIRouter()


def _window(window_minutes: int) -> tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    return end - timedelta(minutes=window_minutes), end


@router.get("/traffic/overview")
async def overview(window_minutes: int = Query(60, gt=0, le=1440)):
    window_start, window_end = _window(window_minutes)
    async with get_pool().acquire() as conn:
        count = await repo.count_distinct_tracks(conn, None, window_start, window_end)
        metrics = compute_metrics(count, window_minutes)
        row = await repo.insert_aggregate(conn, None, None, window_start, window_end, metrics)
    return envelope(row)


@router.get("/traffic/cameras")
async def by_camera(window_minutes: int = Query(60, gt=0, le=1440)):
    window_start, window_end = _window(window_minutes)
    async with get_pool().acquire() as conn:
        cameras = await repo.list_active_cameras(conn)
        results = []
        for cam in cameras:
            count = await repo.count_distinct_tracks(conn, cam["id"], window_start, window_end)
            metrics = compute_metrics(count, window_minutes)
            row = await repo.insert_aggregate(
                conn, cam["id"], cam["road_segment_id"], window_start, window_end, metrics
            )
            results.append({**row, "name": cam["name"]})
    return envelope(results)


@router.get("/traffic/segments")
async def by_segment(window_minutes: int = Query(60, gt=0, le=1440)):
    window_start, window_end = _window(window_minutes)
    async with get_pool().acquire() as conn:
        cameras = await repo.list_active_cameras(conn)

        segments: dict[str, list[dict]] = defaultdict(list)
        for cam in cameras:
            if cam["road_segment_id"]:
                segments[cam["road_segment_id"]].append(cam)

        results = []
        for segment_id, cams in segments.items():
            total = 0
            for cam in cams:
                total += await repo.count_distinct_tracks(conn, cam["id"], window_start, window_end)
            metrics = compute_metrics(total, window_minutes)
            row = await repo.insert_aggregate(conn, None, segment_id, window_start, window_end, metrics)
            results.append({
                **row,
                "cameras": [{"id": c["id"], "name": c["name"],
                            "latitude": c["latitude"], "longitude": c["longitude"]} for c in cams],
            })
    return envelope(results)


# TODO: GET /traffic/history — read stored traffic_aggregates rows over a
# date range, filtered by camera_id or segment_id, paginated. See the TODO
# in repositories/traffic.py for the query this needs.

@router.get("/traffic/history")
async def history(
    camera_id: str | None=None,
    segment_id: str | None=None,
    start_time: datetime | None=None,
    end_time: datetime | None=None,
    limit: int = Query(50,le=200),
    offset: int=0 
):
    if start_time is not None and end_time is not None:
        if start_time>end_time:
            raise ApiError(
                400,
                "INVALID_DATE_RANGE",
                "start_time must be before or equal to end_time",
            )
    async with get_pool().acquire() as conn:
        rows=await repo.list_history(
            conn,camera_id,segment_id,start_time,end_time,limit,offset
        )    
    return envelope(rows)
