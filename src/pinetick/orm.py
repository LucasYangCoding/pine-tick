from sqlalchemy import Column, Integer, DateTime, String
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class TickerLog(Base):
    __tablename__ = "ticker_log"
    id = Column("id", Integer, primary_key=True, comment="id")
    executed_at = Column("executed_at", DateTime, comment="executed_at")
    task_name = Column("task_name", String, comment="task_name")
    status = Column("status", String, comment="status")
    message = Column("message", String, comment="message")
