import asyncio
import traceback
import health_reader
import log_reader
import daemon
import logging
import os
import traceback

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)


async def run():
    queue = asyncio.Queue()
    await asyncio.gather(daemon.connect_server(),
                         rerun_on_exception(log_reader.consume, queue),
                         # rerun_on_exception(log_reader.preprocess, queue),
                         rerun_on_exception(daemon.run),
                         rerun_on_exception(log_reader.produce, queue),
                         rerun_on_exception(health_reader.query_nvml_health)
                         )


async def rerun_on_exception(coro, *args, **kwargs):
    while True:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            # don't interfere with cancellations
            raise
        except Exception:
            print("Caught exception")
            traceback.print_exc()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
