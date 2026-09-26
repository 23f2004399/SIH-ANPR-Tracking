from datetime import datetime

from pydantic import BaseModel


class TrafficAggregateOut(BaseModel):
    camera_id: str | None
    segment_id: str | None
    window_start: datetime
    window_end: datetime
    vehicle_count: int
    density_metric: float | None
    average_speed: float | None
    congestion_level: str | None
    computed_at: datetime
