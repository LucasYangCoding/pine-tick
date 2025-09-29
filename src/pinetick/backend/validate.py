from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ScheduleParams(BaseModel):
    interval: Optional[int] = Field(None, ge=1, description="interval")
    time_point: Optional[time] = Field(None, description="time_point")

    @model_validator(mode="after")
    def check_exclusive(self):
        if not (bool(self.interval) ^ bool(self.time_point)):
            raise ValueError("必须且只能指定 interval 或 time_point 其中之一")
        return self
