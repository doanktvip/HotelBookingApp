from datetime import datetime, timezone, timedelta


def get_vn_time():
    return datetime.now(timezone(timedelta(hours=7)))
