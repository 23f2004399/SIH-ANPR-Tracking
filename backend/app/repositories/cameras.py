import asyncpg

from backend.app.schemas.camera import CameraIn


async def create_camera(conn: asyncpg.Connection, camera: CameraIn) -> dict:
    row = await conn.fetchrow(
        """
        insert into cameras (id, name, latitude, longitude, location_label, road_segment_id, is_active)
        values ($1, $2, $3, $4, $5, $6, $7)
        on conflict (id) do update set
            name = excluded.name, latitude = excluded.latitude, longitude = excluded.longitude,
            location_label = excluded.location_label, road_segment_id = excluded.road_segment_id,
            is_active = excluded.is_active
        returning id, name, latitude, longitude, location_label, road_segment_id, is_active, created_at
        """,
        camera.id, camera.name, camera.latitude, camera.longitude,
        camera.location_label, camera.road_segment_id, camera.is_active,
    )
    return dict(row)


async def list_cameras(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "select id, name, latitude, longitude, location_label, road_segment_id, is_active, created_at "
        "from cameras order by id"
    )
    return [dict(r) for r in rows]
