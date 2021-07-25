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

logger = logger.getLogger(__name__)

invalid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>reject)")
valid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>accept)")
log_dir = 'data/logs' if os.getenv('LOCAL') == 'true' else '../logs'


def start_mining(queue):
    # gminer must be run from a bash script otherwise it will complain about hacking (?!?!?!)
    logger.info('Starting mining')
    cmd = './start-mining.sh'
    miner_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    thread = Thread(target=produce, args=[miner_process.stdout, queue])
    thread.daemon = True
    thread.start()

    miner_process.wait()
    thread.join(timeout=1)


def produce(stdout, queue):
    ''' needs to be in a thread so we can read the stdout w/o blocking '''
    while True:
        line = non_block_read(stdout)
        if line:
            line = strip_color(line.decode('utf-8').rstrip('\n'))
            logger.debug(line)
            share_result = parse_line(line)
            if share_result:
                logger.info(f"producing {line}")
                queue.put(share_result)


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
