import configparser
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from backend.app.core.errors import envelope

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[4]
CONFIG_FILE = BASE_DIR / "configs" / "camera_recordings_config.txt"


def get_camera_video_path(camera_id: str) -> Optional[Path]:
    """
    Parses configs/camera_recordings_config.txt to find the configured recording path
    for the given camera. Prioritizes a web-compatible H.264 version if available.
    """
    if not CONFIG_FILE.exists():
        return None

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    if not config.has_section(camera_id):
        return None

    raw_rel = config.get(camera_id, "video_path", fallback="").strip()
    if not raw_rel:
        return None

    target_path = (BASE_DIR / raw_rel).resolve()

    # Check if a web-compatible H.264 file exists alongside the configured file
    h264_candidate = target_path.with_name(f"{target_path.stem}_h264.mp4")
    if h264_candidate.exists():
        return h264_candidate

    if target_path.exists():
        return target_path

    return None


@router.post("/cameras")
async def create_camera(camera: dict):
    return envelope({})


@router.get("/cameras")
async def list_cameras():
    cameras_data = []
    try:
        from backend.app.core.db import get_pool
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, name, latitude, longitude, location_label, road_segment_id, is_active FROM cameras ORDER BY id"
            )
            cameras_data = [dict(r) for r in rows]
    except Exception as e:
        print(f"[cameras] DB fetch fallback triggered: {e}")

    if not cameras_data:
        # Fallback to exact database schema records
        cameras_data = [
            {"id": "Camera_1", "name": "OMR Junction North", "latitude": 12.9854222, "longitude": 80.2406222},
            {"id": "Camera_2", "name": "OMR Mid Corridor", "latitude": 12.9843556, "longitude": 80.2402417},
            {"id": "Camera_3", "name": "OMR Junction South", "latitude": 12.9845750, "longitude": 80.2398417},
            {"id": "Camera_4", "name": "Velachery Link East", "latitude": 12.9862944, "longitude": 80.2258750},
            {"id": "Camera_5", "name": "Velachery Junction South", "latitude": 12.9864611, "longitude": 80.2229444},
            {"id": "Camera_6", "name": "Velachery Junction North", "latitude": 12.9877000, "longitude": 80.2231361},
        ]

    for cam in cameras_data:
        cam["stream_url"] = f"/api/v1/cameras/{cam['id']}/stream"

    return envelope(cameras_data)


@router.get("/cameras/{camera_id}/stream")
async def stream_camera_feed(camera_id: str):
    """
    Streams the annotated video recording for the specified camera.
    Supports HTTP Range requests for seamless browser seeking and playback.
    """
    video_path = get_camera_video_path(camera_id)
    if not video_path or not video_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Video feed not found for camera '{camera_id}'. Verify configs/camera_recordings_config.txt."
        )

    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        headers={"Accept-Ranges": "bytes"}
    )
