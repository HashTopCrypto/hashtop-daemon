import os
import time
import regex as re
import datetime
import pytz
from tzlocal import get_localzone
import websocket_client
from base_logger import logger
from colors import strip_color
import fcntl
import subprocess
from threading import Thread
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
from helpers import run_with_sudo

#rotating_handler = TimedRotatingFileHandler('gminer.log', 'D', 7, backupCount=1)
# keep 4, 5gb log files
rotating_handler = RotatingFileHandler('gminer.log', maxBytes=5368709120, backupCount=4)
gminer_logger = logger.getLogger(__name__)
gminer_logger.addHandler(rotating_handler)
gminer_logger.propagate = False
logger = logger.getLogger(__name__)

invalid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>reject)")
valid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>accept)")
log_dir = 'data/logs' if os.getenv('LOCAL') == 'true' else '../logs'
INVALIDS_BEFORE_RESTART = 5
total_invalid = 0


def start_mining(gminer_lines):
    # gminer must be run from a bash script otherwise it will complain about hacking (?!?!?!)
    logger.info('Starting mining')
    cmd = './start-mining.sh'
    miner_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    thread = Thread(target=produce, args=[miner_process.stdout, gminer_lines])
    thread.daemon = True
    thread.start()

    miner_process.wait()
    thread.join(timeout=1)


def produce(stdout, gminer_lines):
    ''' needs to be in a thread so we can read the stdout w/o blocking '''
    while True:
        line = non_block_read(stdout)
        if line:
            line = strip_color(line.decode('utf-8').rstrip('\n'))
            logger.debug(line)
            # write the line to the rotating log
            gminer_logger.info(line)
            share_result = parse_line(line)
            check_invalids(share_result)
            if share_result:
                logger.info(f"producing {line}")
                gminer_lines.put(share_result)


async def consume(queue):
    while True:
        # wait for an item from the producer
        item = await queue.get()

        # process the item
        logger.info(f"consuming {item}")

        # send the share data to the backend to be put into the db
        await websocket_client.send_share_update(item)

    # Notify the queue that the item has been processed
    queue.task_done()

def check_invalids(share):
    global total_invalid
    if share['share_type'] == 'invalid':
        total_invalid += 1
        if total_invalid >= INVALIDS_BEFORE_RESTART:
            gminer_logger.error(f'{INVALIDS_BEFORE_RESTART} invalid shares detected, restarting now')
            logger.error(f'{INVALIDS_BEFORE_RESTART} invalid shares detected, restarting now')
            run_with_sudo('reboot now')

def non_block_read(output):
    ''' even in a thread, a normal read with block until the buffer is full '''
    fd = output.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    try:
        return output.read()
    except:
        return ''


def parse_line(line: str) -> dict:
    # reading line by line so we can match once
    invalid = re.search(pattern=invalid_shares, string=line)
    valid = re.search(pattern=valid_shares, string=line)

    # only return a dict if the line read is a share status line
    if invalid or valid:
        match = valid if valid else invalid
        log_time = datetime.datetime.strptime(match.group('time'), "%H:%M:%S").time()
        ts = create_timestamp(log_time)
        share_type = 'valid' if match.group('status') == 'accept' else 'invalid'
        logger.info(share_type)
        return {
            'share_type': share_type,
            'gpu_no': match.group('gpu_no'),
            'timestamp': ts
        }
    else:
        return None


def create_timestamp(log_time: time) -> datetime:
    # get local timezone
    local_tz = get_localzone()

    # combine the local date with the local time from the log file, and set the local timezone
    local_logdt = datetime.datetime.combine(datetime.date.today(), log_time)
    local_logdt = local_tz.localize(local_logdt)

    # create a utc timestamp
    utc_dt = local_logdt.astimezone(pytz.utc)
    return int(utc_dt.timestamp())
