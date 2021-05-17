import glob
import os
import asyncio
import time
import aiofiles
from watchgod import awatch
import regex as re

import daemon
from main import LOGLEVEL

invalid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d).*(?<status>failed)")
valid_shares = re.compile(r"(?<time>\d\d:\d\d:\d\d).*GPU(?<gpu_no>\d).*(?<status>accept)")
log_dir = 'data/logs'
newest = max(glob.iglob(log_dir + '/*.log'), key=os.path.getctime)
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
                print(f"producing {log_line}")
            await queue.put(share_result)


async def consume(queue):
    while True:
        # wait for an item from the producer
        item = await queue.get()

        # process the item
        if LOGLEVEL == "DEBUG":
            print(f'consuming {item}...')\

        await daemon.send_health_update(item)

        # Notify the queue that the item has been processed
        queue.task_done()


async def get_last_line(file):
    with open(file, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()
    return last_line


def parse_line(line: str) -> dict:
    # reading line by line so we can match once
    invalid = re.match(pattern=invalid_shares, string=line)
    valid = re.match(pattern=valid_shares, string=line)

    # only return a dict if the line read is a share status line
    if invalid or valid:
        match = valid if valid else invalid
        return {
            'share_status': match.group('status'),
            'gpu_no': match.group('gpu_no'),
            'time': match.group('time')
        }
    else:
        return None
