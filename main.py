import asyncio
import traceback
import health_reader
import log_reader
import daemon
import os

from base_logger import logger
from dotenv import load_dotenv
load_dotenv()


logger = logger.getLogger(__name__)

async def run():
    queue = asyncio.Queue()
    await asyncio.gather(daemon.connect_server(),
                         rerun_on_exception(log_reader.consume, queue),
                         rerun_on_exception(daemon.run),
                         rerun_on_exception(log_reader.produce, queue),
                         rerun_on_exception(health_reader.query_all_health),
                         )


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
            #traceback.print_exc()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
