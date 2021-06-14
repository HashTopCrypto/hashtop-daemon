import datetime
import time
from tzlocal import get_localzone
import pytz

def create_timestamp(log_time: time) -> datetime:
    # get local timezone
    local_tz = get_localzone()

    # combine the local date with the local time from the log file, and set the local timezone
    local_logdt = datetime.datetime.combine(datetime.date.today(), log_time)
    local_logdt = local_tz.localize(local_logdt)

    # create a utc timestamp
    utc_dt = local_logdt.astimezone(pytz.utc)
    return int(utc_dt.timestamp())