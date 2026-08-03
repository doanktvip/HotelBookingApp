from datetime import datetime, timezone, timedelta

def get_vn_time():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)

def parse_time(time_str):
    return datetime.strptime(time_str, '%H:%M').time()