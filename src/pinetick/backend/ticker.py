import functools
import importlib
import threading
from datetime import datetime, timedelta, time
from typing import Optional, Tuple

import uvicorn
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from fastapi import FastAPI, Request
from sqlalchemy import create_engine, Engine, exists
from sqlalchemy.orm import sessionmaker, Session

from pinetick.backend.api import router
from pinetick.backend.orm import Base, TickerLog
from pinetick.backend.utils import datetime_with_tz, date_with_tz
from pinetick.backend.validate import ScheduleParams


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
        self._scan_lock = threading.Lock()
        self._app = FastAPI()
        self._app.middleware("http")(self._db_middleware)
        self._app.include_router(router)
        self._create_db()

    async def _db_middleware(self, request: Request, call_next):
        request.state.db = self._session()
        try:
            response = await call_next(request)
            request.state.db.commit()
        except Exception as e:
            request.state.db.rollback()
            raise e
        finally:
            request.state.db.close()
        return response

    def _create_db(self):
        """初始化数据库"""
        Base.metadata.create_all(bind=self._engine)

    @staticmethod
    def _compute_trigger_and_start_at(
            *,
            params: Optional[ScheduleParams]=None,
            task: Optional[TickerLog]=None
    ) -> Tuple[str, datetime]:
        if params is not None:
            if params.interval is not None:
                trigger = "interval"
                start_at = datetime_with_tz() + timedelta(seconds=params.interval)
            else:
                trigger = "time"
                start_at = datetime.combine(date_with_tz(), params.time_point)
            return trigger, start_at
        else:
            if task.trigger == "interval":
                start_at = datetime_with_tz() + (task.start_at - task.created_at)
            else:
                start_at = task.start_at + timedelta(days=1)
            return "", start_at

    def schedule(
            self,
            *,
            interval: Optional[int] = None,
            time_point: Optional[time] = None,
    ):
        """定时任务
        时间间隔：执行成功，更新执行时间。执行失败
        时间点：
        """
        params = ScheduleParams(interval=interval, time_point=time_point)
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func_path = func.__module__ + '.' + func.__name__
                with self._session.begin() as db:
                    if not db.query(exists().where(TickerLog.func_path == func_path)).scalar():
                        trigger, start_at = self._compute_trigger_and_start_at(params=params)
                        task = TickerLog(trigger=trigger, start_at=start_at,
                                         func_path=func_path, args=args, kwargs=kwargs)
                        db.add(task)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def _add_task(self, *, db: Session, task: Optional[TickerLog]):
        """添加任务"""
        _, start_at = self._compute_trigger_and_start_at(task=task)
        t = TickerLog(created_at=datetime_with_tz(), trigger=task.trigger, start_at=start_at,
                      func_path=task.func_path, args=task.args, kwargs=task.kwargs)
        db.add(t)

    @staticmethod
    def _func(*, task: Optional[TickerLog]):
        """获取函数"""
        func_path, args, kwargs = task.func_path, task.args, task.kwargs
        module_name, func_name = func_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, func_name)

    def _message(self, *, task: Optional[TickerLog]):
        """执行函数"""
        func = self._func(task=task)
        return func(*(task.args or []), **(task.kwargs or {}))

    def _job(self, *, task_id: int):
        """任务"""
        with self._session.begin() as db:
            try:
                task = db.get(TickerLog, task_id)
                task.message = self._message(task=task)
                task.status = "success"
                self._add_task(db=db, task=task)
            except Exception as e:
                task.message = str(e)
                task.status = "error"
            finally:
                task.end_at = datetime_with_tz()

    def _scan_jobs(self, *, scheduler: BlockingScheduler):
        """扫描数据库任务"""
        with self._scan_lock:
            with self._session.begin() as db:
                tasks = db.query(TickerLog).filter(TickerLog.status.is_(None), TickerLog.is_scan.is_(False)).all()
                for task in tasks:
                    scheduler.add_job(self._job, "date", run_date=task.start_at, kwargs={"task_id": task.id})
                    task.is_scan =  True

    def start(self):
        """启动"""
        executors = {"default": ThreadPoolExecutor(max_workers=4)}
        # scheduler = BlockingScheduler(executors=executors)
        scheduler = BackgroundScheduler(executors=executors)
        scheduler.add_job(self._scan_jobs, "interval", seconds=3, kwargs={"scheduler": scheduler})
        scheduler.start()
        uvicorn.run(self._app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    user, password, host, port, db = "pine_tick", "password", "localhost", "25432", "pine_tick"
    ticker = Ticker(database_url=f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
    @ticker.schedule(interval=10)
    def test1():
        return "test1"

    @ticker.schedule(interval=10)
    def test2():
        return "test2"

    test1()
    test2()
    ticker.start()
