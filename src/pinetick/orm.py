from sqlalchemy import Column, Integer, DateTime, String, JSON
from sqlalchemy.orm import declarative_base

from pinetick.utils import datetime_with_tz

Base = declarative_base()


class TickerLog(Base):
    __tablename__ = "ticker_log"
    id = Column("id", Integer, primary_key=True, comment="id")
    created_at = Column("created_at", DateTime, default=datetime_with_tz(), comment="created_at")
    executed_start_at = Column("executed_start_at", DateTime, nullable=False, comment="executed_start_at")
    executed_end_at = Column("executed_end_at", DateTime, comment="executed_end_at")
    func_path = Column("func_path", String, nullable=False, comment="func_path")
    args = Column("args", JSON, comment="args")
    kwargs = Column("kwargs", JSON, comment="kwargs")
    status = Column("status", String, comment="status")
    message = Column("message", String, comment="message")
