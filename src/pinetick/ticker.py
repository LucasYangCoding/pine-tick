from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .orm import Base
from .validate import ScheduleParams


class Ticker:
    def __init__(self, database_url="sqlite:///pine_tick.db"):
        self._database_url = database_url
        self._engine = create_engine(self._database_url, echo=False)
        self._session = sessionmaker(bind=self._engine)
        self._create_db()

    def _create_db(self):
        Base.metadata.create_all(bind=self._engine)

    def schedule(self, *, interval=None, time_point=None):
        params = ScheduleParams(interval=interval, time_point=time_point)
        """
        Schedule a ticker job to run every interval seconds.
        可以传时间间隔、时间点
        装饰用户的自定义任务
        :param interval:
        :param time_point:
        :return:
        """
        if interval is None and time_point is None:
            raise ValueError("必须指定 interval 或 time_point")

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            # 记录任务
            self.jobs.append({
                "func": func,
                "interval": interval,
                "time_point": time_point
            })
            return wrapper
        return decorator
