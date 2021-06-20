import datetime
from asyncio import sleep
import aiohttp
import gpustat
import daemon
from main import LOGLEVEL
import time


async def query_all_health():
    await sleep(30)
    nvml_health = await query_nvml_health()
    gpu_hashrate = await query_gminer_hashrate()
    gpu_healths = []
    for health in nvml_health:
        gpu_no = int(health['gpu_no'])
        gpu_healths.append({
            'timestamp': int(time.time()),
            **health,
            'hashrate': gpu_hashrate[gpu_no]
        })
    print(gpu_hashrate)

    await daemon.send_health_update(gpu_healths)


async def query_nvml_health():
    # get a bunch of data from NVML for each GPU and pick the stuff we want
    gpu_stats = []
    for stat in gpustat.new_query():
        gpu_stats.append({
            'gpu_no': stat.index,
            'gpu_name': stat.name,
            'fan_speed': stat.fan_speed,
            'temperature': stat.temperature,
            'power_draw': stat.power_draw,
            'power_limit': stat.power_limit
        })
    if LOGLEVEL == "DEBUG":
        print(gpu_stats)
    return gpu_stats


async def query_gminer_hashrate():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:43111/stat') as response:
            if response.status == 200:
                data = await response.json()
                gpu_hashrate = {}
                for gpu in data.get('devices'):
                    gpu_no = gpu.get('gpu_id')
                    hashrate = gpu.get('speed')
                    gpu_hashrate[gpu_no] = hashrate

                if LOGLEVEL == "DEBUG":
                    print(gpu_hashrate)
                return gpu_hashrate
            else:
                print(response)
