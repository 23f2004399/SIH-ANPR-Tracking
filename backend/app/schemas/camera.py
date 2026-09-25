from datetime import datetime

from pydantic import BaseModel


class CameraIn(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    location_label: str | None = None
    road_segment_id: str | None = None
    is_active: bool = True


class CameraOut(CameraIn):
    created_at: datetime
