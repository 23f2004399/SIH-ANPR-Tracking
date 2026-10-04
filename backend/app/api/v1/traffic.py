from fastapi import APIRouter
from backend.app.core.errors import envelope

router = APIRouter()

@router.get("/traffic/overview")
async def overview():
    return envelope({"total_vehicles": 100, "average_speed": 45, "congestion_level": "Low"})

@router.get("/traffic/cameras")
async def by_camera():
    return envelope([])

@router.get("/traffic/segments")
async def by_segment():
    return envelope([])

@router.get("/traffic/history")
async def history():
    return envelope([])
