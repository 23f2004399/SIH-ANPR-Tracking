import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query
from backend.app.core.errors import envelope

router = APIRouter()

CONFIG_PATH = Path(__file__).resolve().parents[4] / "configs" / "urban_analytics_data.json"

def _load_analytics_data() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


@router.get("/traffic/overview")
async def overview(window_minutes: int = Query(1440, description="Rolling time window in minutes")):
    data = _load_analytics_data()
    overview_data = data.get("overview", {})
    if overview_data:
        # Include full enriched structure with stats, fleet, and suggestions
        result = {
            **overview_data,
            "city": data.get("city", "Chennai — OMR Corridor"),
            "stats": data.get("stats", []),
            "fleet": data.get("fleet", []),
            "suggestions": data.get("suggestions", [])
        }
        return envelope(result)
    
    # Fallback default
    return envelope({
        "vehicle_count": 526563,
        "total_vehicles": 526563,
        "density_metric": 4.9,
        "average_speed": 31.2,
        "congestion_level": "Severe",
        "active_choke_points": 2,
        "total_idle_hours": 7132,
        "total_co2_tons": 1866
    })


@router.get("/traffic/segments")
async def by_segment(window_minutes: int = Query(1440, description="Rolling time window in minutes")):
    data = _load_analytics_data()
    segments = data.get("segments", [])
    if segments:
        return envelope(segments)
    
    return envelope([])


@router.get("/traffic/cameras")
async def by_camera(window_minutes: int = Query(1440, description="Rolling time window in minutes")):
    data = _load_analytics_data()
    cameras = data.get("cameras", [])
    if cameras:
        return envelope(cameras)
    
    return envelope([])


@router.get("/traffic/history")
async def history(
    camera_id: Optional[str] = Query(None, description="Optional camera filter"),
    segment_id: Optional[str] = Query(None, description="Optional road segment filter"),
    limit: int = Query(100, description="Max history records")
):
    data = _load_analytics_data()
    hourly = data.get("hourly_aggregates", [])
    if camera_id:
        hourly = [h for h in hourly if h.get("camera_id") == camera_id]
    if segment_id:
        hourly = [h for h in hourly if h.get("segment_id") == segment_id]
    
    return envelope(hourly[:limit])
