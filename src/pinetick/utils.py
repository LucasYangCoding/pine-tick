from datetime import datetime
from zoneinfo import ZoneInfo


def datetime_with_tz():
    return datetime.now(ZoneInfo("Asia/Shanghai"))
