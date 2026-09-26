import re
import asyncpg
from typing import List, Dict, Any

from backend.app.repositories import vehicles as repo

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
    
    return await repo.search_plates(conn, normalized_query, exact, limit)

async def get_vehicle_timeline(conn: asyncpg.Connection, track_id: int) -> Dict[str, Any]:
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
    # 1. Get the primary embedding for this track
    embedding = await repo.get_primary_embedding(conn, track_id)
    if not embedding:
        raise ValueError(f"No Re-ID embedding found for track_id {track_id}")
        
    # 2. Perform the vector similarity search
    # We ask for limit + 1 because the query track itself will likely be returned as the top match
    results = await repo.search_similar_vehicles(conn, embedding, limit + 1)
    
    # Filter out the query track itself
    filtered_results = [r for r in results if r["track_id"] != track_id]
    
    return filtered_results[:limit]
