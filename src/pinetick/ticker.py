import functools
import importlib
from datetime import datetime, timedelta, time
from typing import Optional

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import create_engine, Engine, exists
from sqlalchemy.orm import sessionmaker

from pinetick.orm import Base, TickerLog
from pinetick.utils import datetime_with_tz
from pinetick.validate import ScheduleParams


class Ticker:

    def __init__(
            self,
            *,
            database_url: str,
            engine: Optional[Engine] = None,
            session: Optional[sessionmaker] = None
    ):
        """持久化"""
        self._database_url = database_url
        self._engine = create_engine(self._database_url, echo=False) if engine is None else engine
        self._session = sessionmaker(bind=self._engine) if session is None else session
        self._create_db()

    def _create_db(self):
        """初始化数据库"""
        Base.metadata.create_all(bind=self._engine)

    def schedule(
            self,
            *,
            interval: Optional[int] = None,
            time_point: Optional[datetime] = None,
    ):
        """定时任务"""
        params = ScheduleParams(interval=interval, time_point=time_point)
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if params.interval is not None:
                    executed_start_at = datetime_with_tz() + timedelta(seconds=params.interval)
                else:
                    executed_start_at = params.time_point
                func_path = func.__module__ + '.' + func.__name__
                with self._session.begin() as db:
                    if not db.query(exists().where(TickerLog.func_path == func_path)).scalar():
                        ticker_log = TickerLog(executed_start_at=executed_start_at,
                                               func_path=func_path, args=args, kwargs=kwargs)
                        db.add(ticker_log)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def start(self):
        """启动"""
        executors = {'default': ThreadPoolExecutor(max_workers=4)}
        scheduler = BlockingScheduler(executors=executors)
        with self._session.begin() as db:
            tasks = db.query(TickerLog).filter(TickerLog.status.is_(None)).all()
            for task in tasks:
                func_path, args, kwargs = task.func_path, task.args, task.kwargs
                module_name, func_name = func_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                func = getattr(module, func_name)
                def job(task_id = task.id):
                    with self._session.begin() as inner_db:
                        try:
                            t = inner_db.get(TickerLog, task_id)
                            message = func(*(t.args or []), **(t.kwargs or {}))
                            print(message)
                            t.message = message
                            t.status = "success"
                        except Exception as e:
                            t.message = str(e)
                            t.status = "error"
                        finally:
                            t.executed_end_at = datetime_with_tz()
                scheduler.add_job(job, 'date', run_date=task.executed_start_at)
        scheduler.start()


if __name__ == '__main__':
    ticker = Ticker(database_url='sqlite:///pine_tick.db')
    @ticker.schedule(interval=10)
    def test():
        return 2
    test()
    ticker.start()
