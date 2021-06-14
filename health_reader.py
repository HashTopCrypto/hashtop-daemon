import datetime
from asyncio import sleep

import gpustat
import daemon
from main import LOGLEVEL
import time


async def query_health():
    # get a bunch of data from NVML for each GPU and pick the stuff we want
    await sleep(30)
    gpu_stats = []
    for stat in gpustat.new_query():
        gpu_stats.append({
            'timestamp': int(time.time()),
            'gpu_no': stat.index,
            'gpu_name': stat.name,
            'fan_speed': stat.fan_speed,
            'temperature': stat.temperature,
            'power_draw': stat.power_draw,
            'power_limit': stat.power_limit
        })
    if LOGLEVEL == "DEBUG":
        print(gpu_stats)
    await daemon.send_health_update(gpu_stats)
