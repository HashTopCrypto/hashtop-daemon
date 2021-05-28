import asyncio
import log_reader
import daemon
import logging
import os

LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)


async def run():
    queue = asyncio.Queue()
    await daemon.connect_server()
    await asyncio.gather(log_reader.consume(queue),
                         daemon.run(),
                         log_reader.preprocess(queue),
                         log_reader.produce(queue),
                         )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
