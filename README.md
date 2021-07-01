# hashtop-daemon
Websocket daemon for updating the statistics of a fully managed cryptominer

I wrote this daemon to run on each miner we manage and report vital statistics. It handles connecting to the backend [hashtop-wrangler](https://github.com/HashTopCrypto/hashtop-wrangler)
with websockets and streaming updates about the miners health. Stuff such as valid/invalid shares and hashrate per GPU, each GPUs core clock, memory clock, temp, etc.
I had to learn threading and asynchronous code in python to support non blocking reads from the mining software's stdout (which never ends) while also querying
and sending the health data at the same time.

- `python-socketio` for async websockets to stream data
- `asyncio` for processing and emitting share/health updates as they come with a queue (producer-consumer pattern)
- `subprocess` and `threading` for starting the miner and doing non blocking reads from its stdout. I also use subprocess to run some configuration stuff for the GPUs (overclocks, etc.)
- `janus` for a thread safe queue to use between my async and threaded code (non blocking read on a different thread and async websocket to stream the data)
