from fastapi import APIRouter

from backend.app.core.db import get_pool
from backend.app.core.errors import envelope
from backend.app.repositories import cameras as repo
from backend.app.schemas.camera import CameraIn

router = APIRouter()


@router.post("/cameras")
async def create_camera(camera: CameraIn):
    async with get_pool().acquire() as conn:
        row = await repo.create_camera(conn, camera)
    return envelope(row)


@router.get("/cameras")
async def list_cameras():
    async with get_pool().acquire() as conn:
        rows = await repo.list_cameras(conn)
    return envelope(rows)
