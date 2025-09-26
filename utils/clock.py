import zoneinfo
from datetime import datetime

_EST = zoneinfo.ZoneInfo("America/New_York")


def now_est_str():
    return datetime.now(_EST).strftime("%Y-%m-%d %H:%M:%S")
