import re
import asyncpg
from typing import List, Dict, Any

from backend.app.repositories import vehicles as repo

try:
    from pipeline.config_loader import (
        find_trajectory_by_plate,
        find_trajectory_by_track,
        find_trajectory_by_image,
        get_all_demo_vehicles
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from pipeline.config_loader import (
        find_trajectory_by_plate,
        find_trajectory_by_track,
        find_trajectory_by_image,
        get_all_demo_vehicles
    )

def normalize_plate_text(text: str) -> str:
    """Strips whitespace and non-alphanumeric chars, converts to upper."""
    if not text:
        return ""
    # Remove anything that isn't a letter or number
    normalized = re.sub(r'[^A-Za-z0-9]', '', text)
    return normalized.upper()

async def search_license_plates(conn: asyncpg.Connection, query: str, exact: bool = False, limit: int = 20) -> List[Dict[str, Any]]:
    normalized_query = normalize_plate_text(query)
    if not normalized_query:
        return []

    # Check mock trajectory configuration first
    cfg_veh = find_trajectory_by_plate(normalized_query)
    if cfg_veh:
        hops = cfg_veh["hops"]
        first_hop = hops[0]
        last_hop = hops[-1]
        mock_records = []
        for idx, h in enumerate(hops):
            mock_records.append({
                "id": h.get("track_id", 100 + idx),
                "camera_id": h.get("camera", "Camera_4"),
                "plate_number": cfg_veh["plate"],
                "vehicle_type": cfg_veh["vehicle_type"],
                "color": cfg_veh["color"],
                "first_seen_at": h["datetime"].isoformat(),
                "last_seen_at": (h["datetime"]).isoformat(),
                "route": cfg_veh["route"],
                "total_transit_seconds": cfg_veh["total_transit_seconds"],
                "crop_path": h.get("crop", "")
            })
        return mock_records[:limit]

    if conn is None:
        return []
    return await repo.search_plates(conn, normalized_query, exact, limit)

async def get_vehicle_timeline(conn: asyncpg.Connection, track_id: int) -> Dict[str, Any]:
    # Check mock trajectory configuration
    cfg_veh = find_trajectory_by_track("", track_id)
    if cfg_veh:
        hops = cfg_veh["hops"]
        mock_history = []
        mock_evidence = []
        for idx, h in enumerate(hops):
            mock_history.append({
                "observation_id": 1000 + idx,
                "camera_id": h.get("camera", "Camera_4"),
                "plate_text": cfg_veh["plate"],
                "confidence": 94.5,
                "observed_at": h["datetime"].isoformat(),
                "offset_sec": h.get("offset_sec", 0.0),
                "is_origin": (idx == 0)
            })
            mock_evidence.append({
                "id": 2000 + idx,
                "track_id": track_id,
                "camera_id": h.get("camera", "Camera_4"),
                "crop_path": h.get("crop", ""),
                "asset_type": "vehicle_crop",
                "timestamp": h["datetime"].isoformat()
            })
        return {
            "track_id": track_id,
            "plate": cfg_veh["plate"],
            "route": cfg_veh["route"],
            "total_transit_seconds": cfg_veh["total_transit_seconds"],
            "history": mock_history,
            "evidence": mock_evidence
        }

    if conn is None:
        return {"track_id": track_id, "history": [], "evidence": []}

    history = await repo.get_vehicle_history(conn, track_id)
    assets = await repo.get_vehicle_assets(conn, track_id)

    return {
        "track_id": track_id,
        "history": history,
        "evidence": assets
    }

async def save_vehicle_embedding(conn: asyncpg.Connection, track_id: int, asset_id: int, model_name: str, embedding: List[float], quality_score: float, is_primary: bool) -> dict:
    return await repo.save_embedding(conn, track_id, asset_id, model_name, embedding, quality_score, is_primary)

async def find_similar_vehicles(conn: asyncpg.Connection, track_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    # Check mock trajectory configuration
    cfg_veh = find_trajectory_by_track("", track_id)
    if cfg_veh:
        hops = cfg_veh["hops"]
        other_hops = [h for h in hops if h.get("track_id") != track_id]
        if other_hops:
            mock_similar = []
            for idx, h in enumerate(other_hops):
                mock_similar.append({
                    "track_id": h.get("track_id"),
                    "camera_id": h.get("camera"),
                    "distance": 0.05 + (idx * 0.01),
                    "similarity": 0.95 - (idx * 0.01),
                    "observed_at": h["datetime"].isoformat(),
                    "crop_path": h.get("crop", "")
                })
            return mock_similar[:limit]

    if conn is None:
        return []

    # 1. Get the primary embedding for this track
    embedding = await repo.get_primary_embedding(conn, track_id)
    if not embedding:
        raise ValueError(f"No Re-ID embedding found for track_id {track_id}")

    # 2. Perform the vector similarity search
    results = await repo.search_similar_vehicles(conn, embedding, limit + 1)

    # Filter out the query track itself
    filtered_results = [r for r in results if r["track_id"] != track_id]

    return filtered_results[:limit]
