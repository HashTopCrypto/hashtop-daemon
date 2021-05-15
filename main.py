import asyncio
import time

import log_reader
import daemon


async def run(n):
    queue = asyncio.Queue()
    await asyncio.gather(consume(queue),
                         log_reader.preprocess(queue),
                         log_reader.produce(queue))


async def consume(queue):
    while True:
        # wait for an item from the producer
        item = await queue.get()

        # process the item
        print(f'consuming {item}...')

        # Notify the queue that the item has been processed
        queue.task_done()


def read_file():
    f = open("test", 'r')
    while True:
        line = f.readline()
        if line:
            print(line)
        else:
            time.sleep(0.1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(10))
    loop.close()
