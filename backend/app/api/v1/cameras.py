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
    # Return cameras for Chennai surveillance network with live stream URLs
    cameras_data = [
        {"id": "Camera_1", "name": "OMR Junction North", "latitude": 12.9854, "longitude": 80.2406},
        {"id": "Camera_2", "name": "OMR Mid Corridor", "latitude": 12.9843, "longitude": 80.2402},
        {"id": "Camera_3", "name": "OMR South Exit", "latitude": 12.9830, "longitude": 80.2400},
        {"id": "Camera_4", "name": "NH-45 Main Checkpost", "latitude": 13.0000, "longitude": 80.2000},
        {"id": "Camera_5", "name": "NH-45 South Extension", "latitude": 12.9985, "longitude": 80.2015},
        {"id": "Camera_6", "name": "Velachery Bypass Checkpost", "latitude": 12.9845, "longitude": 80.2398}
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
