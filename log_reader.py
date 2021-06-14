import glob
import os
import asyncio
import time
import aiofiles
from watchgod import awatch
import regex as re
import datetime
import pytz
from tzlocal import get_localzone

import daemon
from main import LOGLEVEL

invalid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>reject)")
valid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d+):.*(?<status>accept)")
log_dir = 'logs'
newest = max(glob.iglob(log_dir + '/*'), key=os.path.getctime)
if LOGLEVEL == "DEBUG":
    print(newest)


async def preprocess(queue):
    # produce only reads changes so we need to preprocess the file
    async with aiofiles.open(newest) as f:
        async for log_line in f:
            share_result = parse_line(log_line)
            if share_result:
                await queue.put(share_result)
                if LOGLEVEL == "DEBUG":
                    print(f"producing {log_line}")


async def produce(queue):
    # read updates from the log asynchronously
    async for changes in awatch(newest):
        log_line = await get_last_line(newest)

        share_result = parse_line(log_line)
        if share_result:
            if LOGLEVEL == "DEBUG":
                print(f"preprocessing {log_line}")
            await queue.put(share_result)


async def consume(queue):
    while True:
        # wait for an item from the producer
        item = await queue.get()

        # process the item
        if LOGLEVEL == "DEBUG":
            print(f'consuming {item}...')

        # send the share data to the backend to be put into the db
        await daemon.send_share_update(item)

    # Notify the queue that the item has been processed
    queue.task_done()


async def get_last_line(file):
    with open(file, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
    if LOGLEVEL == "DEBUG":
        print(last_line)
    return last_line


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
        print(share_type)
        return {
            'sh                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     are_type': share_type,
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
