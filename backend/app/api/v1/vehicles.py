from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Dict, Any
import asyncpg

from backend.app.core.db import get_pool
from backend.app.services import vehicle_service

router = APIRouter()

async def get_db_conn():
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn

@router.get("/search/plate")
async def search_plate(
    q: str = Query(..., min_length=1, description="License plate text to search for"),
    exact: bool = Query(False, description="Whether to perform an exact match"),
    limit: int = Query(20, ge=1, le=100),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    try:
        results = await vehicle_service.search_license_plates(conn, q, exact, limit)
        return {"success": True, "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{track_id}/history")
async def get_history(track_id: int, conn: asyncpg.Connection = Depends(get_db_conn)):
    try:
        timeline = await vehicle_service.get_vehicle_timeline(conn, track_id)
        return {"success": True, "data": timeline["history"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{track_id}/evidence")
async def get_evidence(track_id: int, conn: asyncpg.Connection = Depends(get_db_conn)):
    try:
        timeline = await vehicle_service.get_vehicle_timeline(conn, track_id)
        return {"success": True, "data": timeline["evidence"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{track_id}/similar")
async def get_similar_vehicles(
    track_id: int, 
    limit: int = Query(10, ge=1, le=50),
    conn: asyncpg.Connection = Depends(get_db_conn)
):
    try:
        results = await vehicle_service.find_similar_vehicles(conn, track_id, limit)
        return {"success": True, "data": results}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
