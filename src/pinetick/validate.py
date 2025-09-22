from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ScheduleParams(BaseModel):
    interval: Optional[int] = Field(None, ge=0, description="interval")
    time_point: Optional[datetime] = Field(None, description="time_point")