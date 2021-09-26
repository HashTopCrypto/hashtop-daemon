import asyncio
from time import sleep

import janus
import os
import health_reader
import share_reader
import websocket_client
from helpers import print_subprocess, run_with_sudo
from base_logger import logger
from dotenv import load_dotenv

load_dotenv()

logger = logger.getLogger(__name__)


async def run():
    queue = janus.Queue()

    logger.info('Resetting overclocks')
    print_subprocess(f"echo {os.getenv('SUDO_PASS')} | sudo -S ./reset-oc")
    logger.info('Configuring power limits')
    print_subprocess(f"echo {os.getenv('SUDO_PASS')} | sudo -S ./config-gpus")
    logger.info('Setting fan speeds')
    print_subprocess(f"echo {os.getenv('SUDO_PASS')} | sudo -S ./fan-gpus")

    loop.run_in_executor(None, share_reader.start_mining, queue.sync_q)
    loop.run_in_executor(None, delayed_overclock())
    await asyncio.gather(websocket_client.connect_server(),
                         rerun_on_exception(share_reader.consume, queue.async_q),
                         rerun_on_exception(websocket_client.run),
                         rerun_on_exception(health_reader.query_all_health),
                         )


def delayed_overclock():
    # wait for the dag to be generated before overclocking
    sleep(45)
    logger.info('Overclocking GPUs')
    run_with_sudo("./oc-gpus")


async def rerun_on_exception(coro, *args, **kwargs):
    while True:
        try:
            logger.warning('running coroutine again...')
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            # don't interfere with cancellations
            raise
        except Exception as e:
            logger.error(e, exc_info=True)
            # traceback.print_exc()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(run())
    loop.close()
