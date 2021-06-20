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
    gminer_health = await query_gminer_info()
    gpu_healths = []
    for health in nvml_health:
        gpu_no = int(health['gpu_no'])
        gpu_healths.append({
            'timestamp': int(time.time()),
            **health,
            **gminer_health[gpu_no]
        })

    await daemon.send_health_update(gpu_healths)


async def query_nvml_health():
    # get a bunch of data from NVML for each GPU and pick the stuff we want
    gpu_stats = []
    for stat in gpustat.new_query():
        gpu_stats.append({
            'gpu_no': stat.index,
            'fan_speed': stat.fan_speed,
            'temperature': stat.temperature,
            'power_draw': stat.power_draw,
            'power_limit': stat.power_limit,
            'core_clock': stat.core_clock,
            'mem_clock': stat.mem_clock,
        })
    if LOGLEVEL == "DEBUG":
        print(gpu_stats)
    return gpu_stats


async def query_gminer_info():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://127.0.0.1:43111/stat') as response:
            if response.status == 200:
                data = await response.json()
                gminer_info = {}
                for gpu in data.get('devices'):
                    gpu_no = gpu.get('gpu_id')
                    hashrate = gpu.get('speed')
                    gpu_name = gpu.get('name')
                    gminer_info[gpu_no] = {
                        'hashrate': hashrate,
                        'gpu_name': gpu_name
                    }

                if LOGLEVEL == "DEBUG":
                    print(gminer_info)
                return gminer_info
            else:
                print(response)
