import datetime
import os
import time
from tzlocal import get_localzone
import pytz
import subprocess
from colors import strip_color
from base_logger import logger
from dotenv import load_dotenv

load_dotenv()

logger = logger.getLogger(__name__)

def create_timestamp(log_time: time) -> datetime:
    # get local timezone
    local_tz = get_localzone()

    # combine the local date with the local time from the log file, and set the local timezone
    local_logdt = datetime.datetime.combine(datetime.date.today(), log_time)
    local_logdt = local_tz.localize(local_logdt)

    # create a utc timestamp
    utc_dt = local_logdt.astimezone(pytz.utc)
    return int(utc_dt.timestamp())


def print_subprocess(cmd: str):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in process.stdout:
        if line:
            line = strip_color(line.decode('utf-8').rstrip('\n'))
            logger.debug(line)


def run_with_sudo(cmd: str, *args):
    args_string = " ".join([a for a in args])
    print_subprocess(f"echo {os.getenv('SUDO_PASS')} | sudo -S {cmd} {args_string}")
