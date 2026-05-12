from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SyncStatusResponse(BaseModel):
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    produtos_count: Optional[int] = None
    codigos_count: Optional[int] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class SyncTriggerResponse(BaseModel):
    job_id: str
    status: str
    message: str


class SyncListResponse(BaseModel):
    jobs: list[SyncStatusResponse]
    total: int