from fastapi import APIRouter
from backend.app.core.errors import envelope

router = APIRouter()

@router.post("/cameras")
async def create_camera(camera: dict):
    return envelope({})

@router.get("/cameras")
async def list_cameras():
    # Return dummy cameras for smoke testing
    return envelope([
        {"id": "Camera_1", "name": "OMR Junction North", "latitude": 12.9854, "longitude": 80.2406},
        {"id": "Camera_2", "name": "OMR Mid Corridor", "latitude": 12.9843, "longitude": 80.2402},
        {"id": "Camera_3", "name": "OMR South Exit", "latitude": 12.9830, "longitude": 80.2400},
        {"id": "Camera_4", "name": "NH-45 Main Checkpost", "latitude": 13.0000, "longitude": 80.2000},
        {"id": "Camera_5", "name": "NH-45 South Extension", "latitude": 12.9985, "longitude": 80.2015}
    ])
