from sqlalchemy import Column, Integer, DateTime, String, JSON, Boolean
from sqlalchemy.orm import declarative_base

from pinetick.utils import datetime_with_tz

Base = declarative_base()


class TickerLog(Base):
    __tablename__ = "ticker_log"
    id = Column("id", Integer, primary_key=True, comment="id")
    created_at = Column("created_at", DateTime, default=datetime_with_tz(), comment="created_at")
    trigger = Column("trigger", String, comment="trigger")
    start_at = Column("start_at", DateTime, nullable=False, comment="start_at")
    end_at = Column("end_at", DateTime, comment="end_at")
    func_path = Column("func_path", String, nullable=False, comment="func_path")
    args = Column("args", JSON, comment="args")
    kwargs = Column("kwargs", JSON, comment="kwargs")
    status = Column("status", String, comment="status")
    message = Column("message", String, comment="message")
    is_scan = Column("is_scan", Boolean, default=False, comment="is_scan")
