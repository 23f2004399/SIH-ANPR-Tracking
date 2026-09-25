from datetime import datetime

from pydantic import BaseModel

JOB_STATUSES = ("queued", "processing", "completed", "failed")


class JobIn(BaseModel):
    camera_id: str
    source_file_key: str


class JobOut(BaseModel):
    id: int
    camera_id: str
    source_file_key: str
    status: str
    progress: float
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
